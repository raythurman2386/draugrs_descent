import time
from typing import Dict, List, Optional
import pygame


class PerformanceMonitor:
    """Monitors and reports game performance metrics."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PerformanceMonitor, cls).__new__(cls)
            cls._instance._init_monitor()
        return cls._instance

    def _init_monitor(self) -> None:
        """Initialize the performance monitor."""
        self.frame_times: List[float] = []
        self.max_frame_samples = 120  # 2 seconds at 60 FPS
        self.section_times: Dict[str, List[float]] = {}
        self.current_section: Optional[str] = None
        self.section_start_time = 0.0
        self._font: Optional[pygame.font.Font] = None
        self.show_metrics = False

    def start_frame(self) -> None:
        """Start timing a new frame."""
        self.frame_times.append(time.perf_counter())
        if len(self.frame_times) > self.max_frame_samples:
            self.frame_times.pop(0)

    def start_section(self, name: str) -> None:
        """
        Start timing a section of code.

        Args:
            name: Name of the section to time
        """
        self.current_section = name
        self.section_start_time = time.perf_counter()

    def end_section(self) -> None:
        """End timing the current section."""
        if self.current_section is None:
            return

        elapsed = time.perf_counter() - self.section_start_time
        if self.current_section not in self.section_times:
            self.section_times[self.current_section] = []

        times = self.section_times[self.current_section]
        times.append(elapsed)
        if len(times) > self.max_frame_samples:
            times.pop(0)

        self.current_section = None

    def get_fps(self) -> float:
        """Calculate current FPS based on frame times."""
        if len(self.frame_times) < 2:
            return 0.0

        # Calculate FPS from the last second of frame times
        recent_times = self.frame_times[-60:]  # Last 60 frames
        if len(recent_times) < 2:
            return 0.0

        time_diff = recent_times[-1] - recent_times[0]
        if time_diff <= 0:
            return 0.0

        return (len(recent_times) - 1) / time_diff

    def get_section_stats(self, name: str) -> Dict[str, float]:
        """
        Get statistics for a timed section.

        Args:
            name: Name of the section

        Returns:
            Dictionary containing min, max, and average times
        """
        if name not in self.section_times or not self.section_times[name]:
            return {"min": 0.0, "max": 0.0, "avg": 0.0}

        times = self.section_times[name]
        return {
            "min": min(times) * 1000,  # Convert to milliseconds
            "max": max(times) * 1000,
            "avg": sum(times) / len(times) * 1000,
        }

    def draw_metrics(self, surface: pygame.Surface) -> None:
        """
        Draw performance metrics on screen.

        Args:
            surface: Surface to draw on
        """
        if not self.show_metrics:
            return

        if self._font is None:
            self._font = pygame.font.SysFont(None, 24)

        fps = self.get_fps()
        y = 10

        # Draw FPS
        fps_text = f"FPS: {fps:.1f}"
        fps_surface = self._font.render(fps_text, True, (255, 255, 255))
        surface.blit(fps_surface, (10, y))
        y += 25

        # Draw section times
        for section_name in sorted(self.section_times.keys()):
            stats = self.get_section_stats(section_name)
            stats_text = f"{section_name}: {stats['avg']:.1f}ms"
            stats_surface = self._font.render(stats_text, True, (255, 255, 255))
            surface.blit(stats_surface, (10, y))
            y += 25

    def toggle_metrics_display(self) -> None:
        """Toggle the display of performance metrics."""
        self.show_metrics = not self.show_metrics

    def clear(self) -> None:
        """Clear all performance data."""
        self.frame_times.clear()
        self.section_times.clear()


# Global performance monitor instance
performance = PerformanceMonitor()
