"""Window ownership for live ENGE SPX terminal sessions."""

from PySide6.QtCore import QObject, QPoint, Qt, Signal

from .smart_terminal import TerminalSession, TerminalWindow
from .state import SPXError
from .terminal_preferences import Preferences


class TerminalWorkspace(QObject):
    emptied = Signal()

    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.preferences = Preferences(store, self)
        self.group = None
        self.windows = set()
        self.sidebar_visible = True

    @property
    def sessions(self):
        return tuple(session for window in self.windows for session in window.sessions)

    def _create_window(self, session, *, grouped):
        window = TerminalWindow(workspace=self, grouped=grouped, session=session)
        window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.windows.add(window)
        window.closed.connect(lambda: self._window_closed(window))
        if grouped:
            self.group = window
        return window

    def _put_in_group(self, session):
        if self.group is None:
            self._create_window(session, grouped=True)
        else:
            self.group.add_session(session)
        return self.group

    def open(self, pty, tool, project, *, transfer=None, clipboard=None, session_label=None, reconnect=None):
        session = TerminalSession(pty, tool, project, self.preferences, transfer, clipboard,
                                  session_label=session_label, reconnect=reconnect)
        window = self._put_in_group(session)
        if not session.is_ssh:
            session.view.ended.connect(lambda: self._workspace_session_ended(session))
        window.reveal()
        return session

    def move_session(self, session, source):
        source.remove_session(session)
        try:
            if source.grouped:
                target = self._create_window(session, grouped=False)
                area = source.screen().availableGeometry()
                target.resize(min(950, area.width()), min(670, area.height()))
                desired = source.pos() + QPoint(42, 42)
                target.move(max(area.left(), min(desired.x(), area.right() - target.width() + 1)),
                            max(area.top(), min(desired.y(), area.bottom() - target.height() + 1)))
            else:
                target = self._put_in_group(session)
        except Exception:
            source.add_session(session)
            raise
        target.reveal()
        if not source.sessions:
            source.close()

    def close_session(self, session):
        if session not in self.sessions:
            return
        window = session.window()
        window.remove_session(session)
        session.stop()
        session.deleteLater()
        if not window.sessions:
            window.close()

    def _workspace_session_ended(self, session):
        try:
            state = self.preferences.store.read("runtime.json", {})
        except (OSError, SPXError):
            return
        if isinstance(state, dict) and state.get("phase") == "stopped":
            self.close_session(session)

    def _window_closed(self, window):
        if window is self.group:
            self.group = None
        self.windows.discard(window)
        if not self.windows:
            self.emptied.emit()

    def close(self, *, keep_workspace=False):
        for session in self.sessions:
            if session.is_ssh or not keep_workspace:
                self.close_session(session)
