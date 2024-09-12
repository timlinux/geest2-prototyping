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
    pkgs.python312Packages.debugpy

    # Qt dependencies for X11 backend
    pkgs.qt5.qtbase
    pkgs.qt5.qtx11extras
    pkgs.xorg.libX11
    pkgs.libxkbcommon
    #pkgs.libxkbcommon-x11
    pkgs.freetype
    pkgs.fontconfig
    pkgs.vscode
    pkgs.qtcreator
    pkgs.qgis
    pkgs.gum
  ];

  # Optional: Set up environment variables or commands to run when entering the shell
  shellHook = ''
    echo "GEEST prototyping."
    echo "./generate_model.py - create the model.json by parsing the geest2.ods spreadsheet"
    echo "./validate_model.py - parse the model.json and check it complies to the jsonschema"
    echo "./infer_schema.py - parse the model.json and generate a jsonschema document saved as schema.json"
    echo "./app.py - view the model.json in a Qt5 tree view"
    echo "./run.sh - Run all of the above in sequence"
  '';
  # This is how you set an env var in a shell.nix
  QT_QPA_PLATFORM_PLUGIN_PATH="${pkgs.qt5.qtbase.bin}/lib/qt-${pkgs.qt5.qtbase.version}/plugins/platforms";
  # This is how we can run python that needs QGIS libs
  PYTHONPATH="$PYTHONPATH:${pkgs.qgis}/lib/";
}

