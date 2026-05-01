import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Callable


class CampaignState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class CampaignProgress:
    state: CampaignState = CampaignState.IDLE
    total_leads: int = 0
    sent_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    current_lead: Optional[Dict] = None
    error_message: Optional[str] = None

    @property
    def percentage(self) -> float:
        if self.total_leads == 0:
            return 0.0
        processed = self.sent_count + self.failed_count + self.skipped_count
        return round((processed / self.total_leads) * 100, 1)

    def to_dict(self) -> Dict:
        return {
            "state": self.state.value,
            "total_leads": self.total_leads,
            "sent_count": self.sent_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "current_lead": self.current_lead,
            "error_message": self.error_message,
            "percentage": self.percentage,
        }


class CampaignManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.leads: List[Dict] = []
        self.progress = CampaignProgress()
        self._stop_flag = False
        self._thread: Optional[threading.Thread] = None

    def upload_leads(self, leads: List[Dict]) -> None:
        with self._lock:
            self.leads = leads
            self.progress.total_leads = len(leads)

    def get_leads(self) -> List[Dict]:
        with self._lock:
            return list(self.leads)

    def start_campaign(self, config: Dict) -> tuple:
        with self._lock:
            if self.progress.state == CampaignState.RUNNING:
                return False, "Campaign already in progress"
            if not self.leads:
                return False, "No leads uploaded"
            self._stop_flag = False
            self.progress = CampaignProgress(
                state=CampaignState.RUNNING,
                total_leads=len(self.leads),
            )
        self._thread = threading.Thread(
            target=self._run_campaign, args=(config,), daemon=True
        )
        self._thread.start()
        return True, "Campaign started"

    def stop_campaign(self) -> None:
        with self._lock:
            self._stop_flag = True

    def is_stopped(self) -> bool:
        with self._lock:
            return self._stop_flag

    def get_progress(self) -> Dict:
        with self._lock:
            return self.progress.to_dict()

    def _update_progress(self, event: str, lead: Dict, error: str = None) -> None:
        with self._lock:
            if event == "processing":
                self.progress.current_lead = {"name": lead.get("name", ""), "email": lead.get("email", "")}
            elif event == "sent":
                self.progress.sent_count += 1
                self.progress.current_lead = None
            elif event == "failed":
                self.progress.failed_count += 1
                self.progress.current_lead = None
                if error:
                    self.progress.error_message = error
            elif event == "skipped":
                self.progress.skipped_count += 1

    def _run_campaign(self, config: Dict) -> None:
        from email_adapter import EmailSenderAdapter
        adapter = EmailSenderAdapter(self._update_progress)
        try:
            if not adapter.authenticate():
                with self._lock:
                    self.progress.state = CampaignState.ERROR
                    self.progress.error_message = "Gmail authentication failed"
                return
            adapter.load_sent_log()
            leads = self.get_leads()
            adapter.send_campaign(leads, config, self.is_stopped)
            with self._lock:
                if self._stop_flag:
                    self.progress.state = CampaignState.STOPPED
                else:
                    self.progress.state = CampaignState.COMPLETED
        except Exception as e:
            with self._lock:
                self.progress.state = CampaignState.ERROR
                self.progress.error_message = str(e)
