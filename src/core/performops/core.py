import asyncio
import logging
from typing import Optional

from src.core.performops.analysis import PerformOpsAnalysis
from src.core.performops.judge import PerformOpsJudge
from src.core.performops.model import (
    PerformOpsPlan,
    PerformOpsResult,
    PlannerType,
    ValidationResult,
)
from src.core.performops.planner import PerformOpsPlanner
from src.core.performops.summarizer import PerformOpsSummarizer
from src.core.performops.validator import PerformOpsValidator

logger = logging.getLogger(__name__)

# Self-Refinement 최대 반복 횟수 (초과 시 마지막 plan으로 진행)
MAX_REFINEMENT_ITERATIONS = 3


class PerformOpsCore:
    def __init__(
        self,
        analysis: PerformOpsAnalysis,
        reactive_planner: PerformOpsPlanner,
        proactive_planner: PerformOpsPlanner,
        judge: PerformOpsJudge,
        summarizer: PerformOpsSummarizer,
        validator: Optional[PerformOpsValidator] = None,
    ):
        self._analysis = analysis
        self._reactive_planner = reactive_planner
        self._proactive_planner = proactive_planner
        self._judge = judge
        self._summarizer = summarizer
        self._validator = validator

    async def start(
        self,
        project_id: int,
        app_deployment_name: str,
    ) -> PerformOpsResult:
        # 원인 분석 (데이터 기반 — refinement 대상 아님)
        analysis_result = await self._analysis.analyze(
            project_id=project_id,
            app_deployment_name=app_deployment_name,
        )

        # Self-Refinement 루프: Validator 동의 시까지 반복
        plan, validation_result = await self._refine_plan(
            analysis_result=analysis_result
        )

        if validation_result and not validation_result.approved:
            logger.warning(
                f"[PerformOpsCore] MAX_REFINEMENT_ITERATIONS({MAX_REFINEMENT_ITERATIONS}) "
                f"도달 — 마지막 plan으로 진행."
            )

        # 요약 + 심각성 도출
        summary = await self._summarizer.summarize(
            analysis_result=analysis_result,
            plan=plan,
        )

        return PerformOpsResult(
            project_id=project_id,
            app_deployment_name=app_deployment_name,
            analysis_result=analysis_result,
            plan=plan,
            summary=summary,
        )

    async def _refine_plan(
        self,
        analysis_result,
    ) -> tuple[PerformOpsPlan, Optional[ValidationResult]]:
        """
        매 iteration:
          1. Reactive / Proactive 두 plan을 병렬 생성
          2. Judge가 현재 상황에 더 적합한 plan 선택
          3. Validator가 선택된 plan 검증
             - 통과 → 반환
             - 실패 → 선택된 관점에만 feedback 주입 후 재시도
        """
        reactive_feedback: Optional[str] = None
        proactive_feedback: Optional[str] = None
        last_validation: Optional[ValidationResult] = None
        plan: Optional[PerformOpsPlan] = None

        for iteration in range(1, MAX_REFINEMENT_ITERATIONS + 1):
            logger.info(
                f"[PerformOpsCore] Self-Refinement iteration {iteration}/{MAX_REFINEMENT_ITERATIONS}"
            )

            # ── 1. 두 관점 plan 병렬 생성 ──
            reactive_plan, proactive_plan = await asyncio.gather(
                self._reactive_planner.plan(
                    analysis_result=analysis_result,
                    feedback=reactive_feedback,
                ),
                self._proactive_planner.plan(
                    analysis_result=analysis_result,
                    feedback=proactive_feedback,
                ),
            )

            # ── 2. Judge: 더 적합한 plan 선택 ──
            judge_result = await self._judge.judge(
                analysis_result=analysis_result,
                reactive_plan=reactive_plan,
                proactive_plan=proactive_plan,
            )

            plan = (
                reactive_plan
                if judge_result.selected == PlannerType.REACTIVE
                else proactive_plan
            )

            logger.info(
                f"[PerformOpsCore] Judge selected={judge_result.selected} "
                f"reason={judge_result.reason!r}"
            )

            # ── 3. Validator 없으면 즉시 반환 ──
            if self._validator is None:
                return plan, None

            # ── 4. Validator: 선택된 plan 검증 ──
            validation_result = await self._validator.validate(
                analysis_result=analysis_result,
                plan=plan,
            )
            last_validation = validation_result

            self._log_validation(iteration, judge_result.selected, validation_result)

            if validation_result.approved:
                logger.info(
                    f"[PerformOpsCore] Validator APPROVED at iteration {iteration}."
                )
                return plan, validation_result

            # ── 5. 거절 시 선택된 관점에만 feedback 주입 ──
            if judge_result.selected == PlannerType.REACTIVE:
                reactive_feedback = validation_result.feedback
            else:
                proactive_feedback = validation_result.feedback

        assert plan is not None
        return plan, last_validation

    @staticmethod
    def _log_validation(
        iteration: int,
        selected: PlannerType,
        result: ValidationResult,
    ) -> None:
        rule_summary = ", ".join(
            f"{r.name}={'OK' if r.passed else 'FAIL'}({r.score:.2f})"
            for r in result.rule_results
        )
        logger.info(
            f"[Validator] iter={iteration} selected={selected} "
            f"approved={result.approved} llm_approved={result.llm_approved} "
            f"rules=[{rule_summary}] feedback={result.feedback!r}"
        )
