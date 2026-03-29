import logging
from typing import Optional

from src.core.llm import LLM
from src.core.output_parser import ValidatorOutputParser
from src.core.performops.model import (
    PerformOpsAnalysisResult,
    PerformOpsPlan,
    RuleCheckResult,
    ValidationResult,
)
from src.core.performops.validator import PerformOpsValidator
from src.deps.get_llm import get_llm

logger = logging.getLogger(__name__)

# ── Rule-based 임계값 ────────────────────────────────────────────────────────
API_RESOLVE_RATE_THRESHOLD = 0.8  # http_method 채워진 액션 비율
MIN_ACTION_COUNT = 1  # 최소 액션 수
DANGER_STATES = {"위험", "critical", "oomkill", "oom", "throttle", "오류", "error"}

# ── LLM-as-Judge 프롬프트 ───────────────────────────────────────────────────
JUDGE_PROMPT = """당신은 Kubernetes 성능 운영 시스템의 검증 전문가입니다.
아래 분석 결과와 조치 계획의 일관성을 평가하세요.

## 원인 분석 결과
{analysis_result}

## 리소스 상태 요약
- 프로젝트 리소스: {project_resource}
- App Deployment 리소스: {app_deployment_resource}
- Deployment 상태: {deployment_status}
- Pod 로그: {pod_log}
- 트래픽: {traffic}
- 지연 시간: {latency}

## 조치 계획
{plan_actions}

## 평가 기준
1. 조치 계획이 분석에서 지적한 문제를 실제로 다루고 있는가?
2. 각 조치의 이유(reason)가 분석 결과와 논리적으로 연결되는가?
3. 분석에서 지적된 주요 문제 중 계획에서 누락된 것이 없는가?

위 기준을 바탕으로 평가하고, 아래 JSON 형식으로만 반환하세요.
approved가 false인 경우 feedback에 구체적으로 어떤 점이 부족한지, 재계획 시 무엇을 반드시 포함해야 하는지 작성하세요.

{{
  "approved": true,
  "feedback": "승인된 경우 빈 문자열, 거절된 경우 구체적인 개선 요구사항"
}}"""


def _format_plan_for_judge(plan: PerformOpsPlan) -> str:
    lines = []
    for i, action in enumerate(plan.actions, 1):
        api_info = ""
        if action.http_method and action.http_path:
            api_info = f" → {action.http_method} {action.http_path}"
        lines.append(f"{i}. {action.action} (이유: {action.reason}){api_info}")
    return "\n".join(lines) if lines else "(계획 없음)"


class PerformOpsValidatorImpl(PerformOpsValidator):
    """
    2-layer 검증 구현체.

    Layer 1 - Rule-based (fast gate):
      - api_resolve_rate  : http_method 채워진 비율 ≥ 0.8
      - min_action_count  : 액션 수 ≥ 1
      - no_duplicate      : 동일 http_path+http_body 중복 없음
      - severity_consistent: 위험 키워드 있는데 액션 수 = 0

    Layer 2 - LLM-as-Judge (semantic gate, rule 통과 시에만):
      - 분석 결과와 계획의 semantic 일관성 평가
    """

    def __init__(self, llm: Optional[LLM] = None):
        self._llm = llm or get_llm(template=JUDGE_PROMPT)
        self._parser = ValidatorOutputParser()

    async def validate(
        self,
        analysis_result: PerformOpsAnalysisResult,
        plan: PerformOpsPlan,
    ) -> ValidationResult:

        # Layer 1: Rule-based
        rule_results = self._run_rules(analysis_result, plan)
        failed_rules = [r for r in rule_results if not r.passed]

        if failed_rules:
            feedback = self._build_rule_feedback(failed_rules)
            logger.info(
                f"[Validator] Rule-based FAILED. rules={[r.name for r in failed_rules]}"
            )
            return ValidationResult(
                approved=False,
                feedback=feedback,
                rule_results=rule_results,
                llm_approved=None,
            )

        logger.info("[Validator] Rule-based PASSED. Proceeding to LLM-as-Judge.")

        # Layer 2: LLM-as-Judge
        llm_approved, llm_feedback = await self._run_llm_judge(analysis_result, plan)

        logger.info(f"[Validator] LLM-as-Judge result: approved={llm_approved}")
        return ValidationResult(
            approved=llm_approved,
            feedback=llm_feedback if not llm_approved else "",
            rule_results=rule_results,
            llm_approved=llm_approved,
        )

    # ── Layer 1: Rule-based ─────────────────────────────────────────────────

    def _run_rules(
        self,
        analysis_result: PerformOpsAnalysisResult,
        plan: PerformOpsPlan,
    ) -> list[RuleCheckResult]:
        return [
            self._check_api_resolve_rate(plan),
            self._check_min_action_count(plan),
            self._check_no_duplicate_actions(plan),
            self._check_severity_consistency(analysis_result, plan),
        ]

    def _check_api_resolve_rate(self, plan: PerformOpsPlan) -> RuleCheckResult:
        """http_method가 채워진 액션 비율 ≥ threshold"""
        total = len(plan.actions)
        if total == 0:
            return RuleCheckResult(
                name="api_resolve_rate",
                passed=False,
                score=0.0,
                detail="액션이 없어 API 해석률 계산 불가",
            )
        resolved = sum(1 for a in plan.actions if a.http_method)
        rate = resolved / total
        passed = rate >= API_RESOLVE_RATE_THRESHOLD
        return RuleCheckResult(
            name="api_resolve_rate",
            passed=passed,
            score=rate,
            detail=(
                f"API 해석률 {rate:.0%} ({resolved}/{total})"
                + ("" if passed else f" — 기준 {API_RESOLVE_RATE_THRESHOLD:.0%} 미달")
            ),
        )

    def _check_min_action_count(self, plan: PerformOpsPlan) -> RuleCheckResult:
        """액션 수 ≥ MIN_ACTION_COUNT"""
        count = len(plan.actions)
        passed = count >= MIN_ACTION_COUNT
        return RuleCheckResult(
            name="min_action_count",
            passed=passed,
            score=min(count / MIN_ACTION_COUNT, 1.0),
            detail=(
                f"액션 수 {count}개"
                + ("" if passed else f" — 최소 {MIN_ACTION_COUNT}개 필요")
            ),
        )

    def _check_no_duplicate_actions(self, plan: PerformOpsPlan) -> RuleCheckResult:
        """동일 http_path + http_body 조합 중복 없음"""
        seen: set[tuple[str, str]] = set()
        duplicates: list[str] = []
        for action in plan.actions:
            key = (action.http_path or "", action.http_body or "")
            if key[0] and key in seen:
                duplicates.append(action.http_path or "")
            seen.add(key)

        passed = len(duplicates) == 0
        return RuleCheckResult(
            name="no_duplicate_actions",
            passed=passed,
            score=0.0 if duplicates else 1.0,
            detail=(
                "중복 액션 없음"
                if passed
                else f"중복 액션 발견: {', '.join(set(duplicates))}"
            ),
        )

    def _check_severity_consistency(
        self,
        analysis_result: PerformOpsAnalysisResult,
        plan: PerformOpsPlan,
    ) -> RuleCheckResult:
        """
        분석 결과에 위험 상태 키워드가 있을 때 액션이 존재하는지 확인.
        """
        resource = analysis_result.resource
        all_states = " ".join(
            [
                resource.project_resource.state,
                resource.app_deployment_resource.state,
                resource.deployment_status.state,
                resource.pod_log.state,
                resource.traffic.state,
                resource.latency.state,
            ]
        ).lower()

        has_danger = any(keyword in all_states for keyword in DANGER_STATES)
        has_actions = len(plan.actions) > 0

        if has_danger and not has_actions:
            return RuleCheckResult(
                name="severity_consistency",
                passed=False,
                score=0.0,
                detail="위험 상태가 감지되었으나 조치 계획이 없음",
            )

        return RuleCheckResult(
            name="severity_consistency",
            passed=True,
            score=1.0,
            detail=(
                "위험 상태 감지 → 조치 계획 존재"
                if has_danger
                else "위험 상태 없음 — 일관성 검사 해당 없음"
            ),
        )

    # ── Layer 2: LLM-as-Judge ───────────────────────────────────────────────

    async def _run_llm_judge(
        self,
        analysis_result: PerformOpsAnalysisResult,
        plan: PerformOpsPlan,
    ) -> tuple[bool, str]:
        plan_text = _format_plan_for_judge(plan)
        resource = analysis_result.resource

        try:
            response = await self._llm.chat(
                variables=[
                    analysis_result.result,
                    resource.project_resource,
                    resource.app_deployment_resource,
                    resource.deployment_status,
                    resource.pod_log,
                    resource.traffic,
                    resource.latency,
                    plan_text,
                ],
            )
            return self._parser.parse(response)
        except Exception as e:
            # LLM-as-Judge 실패 시 보수적으로 통과 처리 (운영 중단 방지)
            logger.warning(f"[Validator] LLM-as-Judge 실패, 통과 처리. error={e}")
            return True, ""

    @staticmethod
    def _build_rule_feedback(failed_rules: list[RuleCheckResult]) -> str:
        lines = ["다음 문제를 수정하여 재계획하세요:"]
        for rule in failed_rules:
            lines.append(f"- [{rule.name}] {rule.detail}")
        return "\n".join(lines)
