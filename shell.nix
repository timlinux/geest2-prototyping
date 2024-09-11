{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "pyqt5-json-validation-env";

  # Define the Python version and dependencies
  buildInputs = [
    pkgs.python312                # Use Python 3.12
    pkgs.python312Packages.jsonschema  # Install jsonschema for validation
    pkgs.python312Packages.pyqt5       # Install PyQt5 for the GUI
    pkgs.python312Packages.pandas
    pkgs.python312Packages.odfpy

    # Qt dependencies for X11 backend
    pkgs.qt5.qtbase
    pkgs.qt5.qtx11extras
    pkgs.xorg.libX11
    pkgs.libxkbcommon
    #pkgs.libxkbcommon-x11
    pkgs.freetype
    pkgs.fontconfig
  ];

  # Optional: Set up environment variables or commands to run when entering the shell
  shellHook = ''
    echo "Environment setup for PyQt5 and JSON validation with Python 3.12."
  '';

  QT_QPA_PLATFORM_PLUGIN_PATH="${pkgs.qt5.qtbase.bin}/lib/qt-${pkgs.qt5.qtbase.version}/plugins/platforms";
}

