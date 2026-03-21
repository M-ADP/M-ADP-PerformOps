import asyncio
import json

from src.core.analyzer.metrics import MetricsAnalyzer
from src.core.analyzer.workload_state import WorkLoadStateAnalyzer
from src.core.llm import LLM
from src.core.performops.analysis import PerformOpsAnalysis
from src.core.performops.model import (
    PerformOpsAnalysisResult,
    PerformOpsanalysisResource,
    TrackingMetric,
)
from src.deps.get_llm import get_llm

ANALYSIS_PROMPT = """아래는 {app_deployment_name} (project_id: {project_id})의 현재 상태 데이터입니다.

## 프로젝트 리소스
{project_resource}

## App Deployment 리소스 (CPU/Memory)
CPU: {cpu}
Memory: {memory}
할당량: {app_deployment_resource}

## Deployment 이벤트
{deployment_status}

## Pod 로그
{pod_log}

## 트래픽
{traffic}

## 지연 시간 (P95 latency)
{latency}

각 항목에 대해 현재 상태(state), 변화(change), 판단 근거(basis)를 분석하고
전체 원인 분석 결과(result)를 아래 JSON 형식으로만 반환하세요.

{{
  "result": "전체 원인 분석 요약",
  "project_resource": {{"state": "...", "change": "...", "basis": "..."}},
  "app_deployment_resource": {{"state": "...", "change": "...", "basis": "..."}},
  "deployment_status": {{"state": "...", "change": "...", "basis": "..."}},
  "pod_log": {{"state": "...", "change": "...", "basis": "..."}},
  "traffic": {{"state": "...", "change": "...", "basis": "..."}},
  "latency": {{"state": "...", "change": "...", "basis": "..."}}
}}"""


class PerformOpsAnalysisImpl(PerformOpsAnalysis):

    def __init__(
            self,
            metrics_analyzer: MetricsAnalyzer,
            workload_state_analyzer: WorkLoadStateAnalyzer,
            llm: LLM = None,
    ):
        super().__init__(
            metrics_analyzer=metrics_analyzer,
            workload_state_analyzer=workload_state_analyzer,
        )
        self._llm = llm or get_llm()

    async def analyze(
            self,
            project_id: int,
            app_deployment_name: str,
    ) -> PerformOpsAnalysisResult:
        (
            project_resource,
            app_deployment_resource,
            deployment_status,
            pod_log,
            traffic,
            cpu,
            memory,
            latency,
        ) = await asyncio.gather(
            self._workload_state_analyzer.get_project_resource(project_id),
            self._workload_state_analyzer.get_app_deployment_resource(project_id, app_deployment_name),
            self._workload_state_analyzer.get_app_deployment_events(project_id, app_deployment_name),
            self._workload_state_analyzer.get_app_deployment_logs(project_id, app_deployment_name),
            self._metrics_analyzer.get_app_deployment_traffic(project_id, app_deployment_name),
            self._metrics_analyzer.get_app_deployment_cpu(project_id, app_deployment_name),
            self._metrics_analyzer.get_app_deployment_memory(project_id, app_deployment_name),
            self._metrics_analyzer.get_app_deployment_latency(project_id, app_deployment_name),
        )

        prompt = ANALYSIS_PROMPT.format(
            project_id=project_id,
            app_deployment_name=app_deployment_name,
            project_resource=project_resource,
            app_deployment_resource=app_deployment_resource,
            deployment_status=deployment_status,
            pod_log=pod_log,
            traffic=traffic,
            cpu=cpu,
            memory=memory,
            latency=latency,
        )

        response = await self._llm.chat(query=prompt)
        parsed = json.loads(response)

        return PerformOpsAnalysisResult(
            result=parsed["result"],
            resource=PerformOpsanalysisResource(
                project_resource=TrackingMetric(**parsed["project_resource"]),
                app_deployment_resource=TrackingMetric(**parsed["app_deployment_resource"]),
                deployment_status=TrackingMetric(**parsed["deployment_status"]),
                pod_log=TrackingMetric(**parsed["pod_log"]),
                traffic=TrackingMetric(**parsed["traffic"]),
                latency=TrackingMetric(**parsed["latency"]),
            ),
        )
