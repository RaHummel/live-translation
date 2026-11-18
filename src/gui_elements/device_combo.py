from PySide6.QtWidgets import QComboBox


def select_device_in_combo(combo: QComboBox, device_index: int | None, device_name: str | None) -> None:
    """Select a device in combo by index (data), falling back to name (text)."""
    if device_index is not None:
        idx = combo.findData(device_index)
        if idx >= 0:
            combo.setCurrentIndex(idx)
            return
    if device_name:
        combo.setCurrentText(device_name)
