"""Unified Project Size & Storage Analyzer."""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from app.scanner.project_scanner import ScanResult
from app.analyzers.size.file_analyzer import FileSizeAnalyzer, FileSizeAnalysisResult
from app.analyzers.size.directory_analyzer import DirectoryAnalyzer, DirectorySizeInfo
from app.database.models import AnomalyRecord


@dataclass
class SizeAnalysisSummary:
    total_size_bytes: int
    total_files: int
    python_files: int
    directory_count: int
    storage_health_score: int
    top_directories: List[DirectorySizeInfo]
    file_analysis: FileSizeAnalysisResult
    anomalies: List[AnomalyRecord] = field(default_factory=list)


class SizeAnalyzer:
    """Main size analyzer uniting file distribution, directory breakdown, and storage health scoring."""

    def __init__(self, large_file_threshold_mb: int = 50):
        self.file_analyzer = FileSizeAnalyzer(large_file_threshold_mb=large_file_threshold_mb)

    def analyze_scan(self, scan_result: ScanResult) -> SizeAnalysisSummary:
        file_analysis = self.file_analyzer.analyze(scan_result.file_metadatas)
        top_directories = DirectoryAnalyzer.analyze_directories(scan_result.file_metadatas)

        anomalies = list(file_analysis.anomalies)

        # Storage health score calculation (0 - 100)
        health_score = 100
        for anomaly in anomalies:
            if anomaly.severity == "CRITICAL":
                health_score -= 25
            elif anomaly.severity == "HIGH":
                health_score -= 15
            elif anomaly.severity == "MEDIUM":
                health_score -= 10
            elif anomaly.severity == "LOW":
                health_score -= 5

        health_score = max(0, min(100, health_score))

        return SizeAnalysisSummary(
            total_size_bytes=scan_result.total_size_bytes,
            total_files=scan_result.total_files,
            python_files=scan_result.python_files,
            directory_count=scan_result.directory_count,
            storage_health_score=health_score,
            top_directories=top_directories,
            file_analysis=file_analysis,
            anomalies=anomalies
        )
