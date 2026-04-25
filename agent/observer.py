import threading
import time
import psutil
import random
from typing import Callable, List
from dataclasses import dataclass

@dataclass
class ObserverEvent:
    message: str
    priority: str  # "low", "normal", "high"
    category: str # "system", "reminder", "notification"

class BaseObserver:
    """Base class for all proactive observers."""
    def __init__(self, speak_callback: Callable[[str], None]):
        self.speak = speak_callback

    def check(self) -> ObserverEvent | None:
        """Perform the check and return an event if something is noteworthy."""
        raise NotImplementedError("Observers must implement the check() method.")

class SystemObserver(BaseObserver):
    """Monitors system resources and alerts if they are critical."""
    def __init__(self, speak_callback):
        super().__init__(speak_callback)
        self.cpu_threshold = 85.0
        self.ram_threshold = 90.0
        self.last_alert_time = 0
        self.alert_cooldown = 300 # 5 minutes

    def check(self) -> ObserverEvent | None:
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent
        now = time.time()

        if now - self.last_alert_time < self.alert_cooldown:
            return None

        if cpu > self.cpu_threshold:
            self.last_alert_time = now
            return ObserverEvent(
                message=f"Sir, CPU usage is critically high at {cpu}%. You might want to check for runaway processes.",
                priority="high",
                category="system"
            )

        if ram > self.ram_threshold:
            self.last_alert_time = now
            return ObserverEvent(
                message=f"Sir, system memory is almost full ({ram}%). I suggest closing some unused applications.",
                priority="high",
                category="system"
            )

        return None

class BackgroundObserver:
    """Manages and executes all proactive observers in a background thread."""
    def __init__(self, speak_callback: Callable[[str], None]):
        self.speak = speak_callback
        self.observers: List[BaseObserver] = []
        self.running = False
        self._thread = None

    def add_observer(self, observer: BaseObserver):
        self.observers.append(observer)

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="JarvisObserver")
        self._thread.start()
        print("[Observer] 🛰️  Proactive monitoring started.")

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join()

    def _run_loop(self):
        while self.running:
            for observer in self.observers:
                try:
                    event = observer.check()
                    if event:
                        print(f"[Observer] 🔔 Event detected: {event.category} - {event.message}")
                        self.speak(event.message)
                except Exception as e:
                    print(f"[Observer] ⚠️  Error in observer {observer.__class__.__name__}: {e}")

            # Wait before the next round of checks to avoid CPU waste
            time.sleep(30)
