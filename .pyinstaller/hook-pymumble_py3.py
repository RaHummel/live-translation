"""
PyInstaller hook for pymumble workspace dependency.
This ensures pymumble and all its submodules are properly collected.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all pymumble submodules
hiddenimports = collect_submodules('pymumble_py3')

# Collect any data files if needed
datas = collect_data_files('pymumble_py3', include_py_files=True)
