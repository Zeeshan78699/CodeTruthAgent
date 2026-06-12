# framework_signatures.py
# Pure data. No logic.
# CodeTruth Agent V3 — Module 1 — Universal Repository Discovery Engine

# ------------------------------------------------------------------ #
# Application Type Signals                                             #
# ------------------------------------------------------------------ #

PACKAGE_SIGNATURES: dict[str, tuple[str, int]] = {
    # Web Applications
    "django":                ("WEB_APPLICATION",    2),
    "flask":                 ("WEB_APPLICATION",    2),
    "tornado":               ("WEB_APPLICATION",    2),
    "bottle":                ("WEB_APPLICATION",    2),
    "pyramid":               ("WEB_APPLICATION",    2),
    # API Services
    "fastapi":               ("API_SERVICE",        2),
    "starlette":             ("API_SERVICE",        1),
    "aiohttp":               ("API_SERVICE",        1),
    "sanic":                 ("API_SERVICE",        2),
    "litestar":              ("API_SERVICE",        2),
    # CLI Tools
    "click":                 ("CLI_TOOL",           2),
    "typer":                 ("CLI_TOOL",           2),
    "argparse":              ("CLI_TOOL",           1),
    "rich":                  ("CLI_TOOL",           1),
    "prompt_toolkit":        ("CLI_TOOL",           1),
    # ML / AI
    "torch":                 ("ML_PIPELINE",        2),
    "tensorflow":            ("ML_PIPELINE",        2),
    "keras":                 ("ML_PIPELINE",        2),
    "transformers":          ("ML_PIPELINE",        4),   # weight=4 dominates NLP/CV/AUDIO specialist signals
    "scikit_learn":          ("ML_PIPELINE",        2),
    "scikit-learn":          ("ML_PIPELINE",        2),
    "sklearn":               ("ML_PIPELINE",        2),
    "xgboost":               ("ML_PIPELINE",        2),
    "lightgbm":              ("ML_PIPELINE",        2),
    "jax":                   ("ML_PIPELINE",        2),
    "diffusers":             ("ML_PIPELINE",        2),
    # Data Engineering
    "apache_airflow":        ("DATA_ENGINEERING",   2),
    "apache-airflow":        ("DATA_ENGINEERING",   2),
    "airflow":               ("DATA_ENGINEERING",   2),
    "prefect":               ("DATA_ENGINEERING",   2),
    "dagster":               ("DATA_ENGINEERING",   2),
    "dbt":                   ("DATA_ENGINEERING",   2),
    "pyspark":               ("DATA_ENGINEERING",   2),
    "pandas":                ("DATA_ENGINEERING",   1),
    "polars":                ("DATA_ENGINEERING",   1),
    "dask":                  ("DATA_ENGINEERING",   2),
    "great_expectations":    ("DATA_ENGINEERING",   1),
    "great-expectations":    ("DATA_ENGINEERING",   1),
    # Library / Framework
    "setuptools":            ("LIBRARY_FRAMEWORK",  1),
    "flit":                  ("LIBRARY_FRAMEWORK",  1),
    "hatchling":             ("LIBRARY_FRAMEWORK",  1),
    "poetry":                ("LIBRARY_FRAMEWORK",  1),
    # Finance
    "quantlib":              ("FINANCE_SYSTEM",     2),
    "zipline":               ("FINANCE_SYSTEM",     2),
    "backtrader":            ("FINANCE_SYSTEM",     2),
    "ccxt":                  ("FINANCE_SYSTEM",     2),
    "ta_lib":                ("FINANCE_SYSTEM",     2),
    "ta-lib":                ("FINANCE_SYSTEM",     2),
    "yfinance":              ("FINANCE_SYSTEM",     1),
    # DevOps
    "ansible":               ("DEVOPS_TOOLING",     2),
    "fabric":                ("DEVOPS_TOOLING",     2),
    "invoke":                ("DEVOPS_TOOLING",     1),
    "paramiko":              ("DEVOPS_TOOLING",     1),
    "docker":                ("DEVOPS_TOOLING",     1),
    "kubernetes":            ("DEVOPS_TOOLING",     2),
    # Frontend Applications
    "react":              ("FRONTEND_APPLICATION", 2),
    "react-dom":          ("FRONTEND_APPLICATION", 2),
    "react_dom":          ("FRONTEND_APPLICATION", 2),
    "vue":                ("FRONTEND_APPLICATION", 2),
    "angular":            ("FRONTEND_APPLICATION", 2),
    "svelte":             ("FRONTEND_APPLICATION", 2),
    "next":               ("FRONTEND_APPLICATION", 2),
    "gatsby":             ("FRONTEND_APPLICATION", 2),
    "nuxt":               ("FRONTEND_APPLICATION", 2),

    # Java / Spring ecosystem
    "springframework":    ("WEB_APPLICATION",      2),
    "spring_boot":        ("WEB_APPLICATION",      2),
    "spring-boot":        ("WEB_APPLICATION",      2),
    "hibernate":          ("WEB_APPLICATION",      1),
    "micronaut":          ("API_SERVICE",          2),
    "quarkus":            ("API_SERVICE",          2),
    "vertx":              ("API_SERVICE",          2),

    # Search / Data Platforms
    "elasticsearch":      ("DATA_ENGINEERING",     2),
    "opensearch":         ("DATA_ENGINEERING",     2),
    "kibana":             ("DATA_ENGINEERING",     2),

    # Database Systems (Python connectors)
    "redis":              ("DATABASE_SYSTEM",      2),
    "pymongo":            ("DATABASE_SYSTEM",      2),
    "pymysql":            ("DATABASE_SYSTEM",      2),
    "psycopg2":           ("DATABASE_SYSTEM",      2),
    "psycopg":            ("DATABASE_SYSTEM",      2),
    "motor":              ("DATABASE_SYSTEM",      2),   # async MongoDB
    "cassandra_driver":   ("DATABASE_SYSTEM",      2),
    "cassandra-driver":   ("DATABASE_SYSTEM",      2),
    "neo4j":              ("DATABASE_SYSTEM",      2),
    "influxdb":           ("DATABASE_SYSTEM",      2),
    "arangodb":           ("DATABASE_SYSTEM",      2),

    # Compiler / Toolchain / Language Runtime
    "llvmlite":           ("COMPILER_TOOLCHAIN",   2),
    "clang":              ("COMPILER_TOOLCHAIN",   2),

    # Game Engine
    "pygame":             ("GAME_ENGINE",          2),
    "panda3d":            ("GAME_ENGINE",          2),
    "arcade":             ("GAME_ENGINE",          2),
    "godot":              ("GAME_ENGINE",          2),

    # Embedded / IoT
    "micropython":        ("EMBEDDED_SYSTEM",      2),
    "circuitpython":      ("EMBEDDED_SYSTEM",      2),
    "rpi_gpio":           ("EMBEDDED_SYSTEM",      2),
    "rpi-gpio":           ("EMBEDDED_SYSTEM",      2),
    "smbus":              ("EMBEDDED_SYSTEM",      1),
    "serial":             ("EMBEDDED_SYSTEM",      1),

    # Code Governance
    "sentence_transformers": ("CODE_GOVERNANCE",    2),
    "sentence-transformers": ("CODE_GOVERNANCE",    2),

    # CAD / Engineering Design
    "ezdxf":           ("CAD_SYSTEM",          2),   # AutoCAD DXF
    "pyautocad":       ("CAD_SYSTEM",          2),   # AutoCAD automation
    "ifcopenshell":    ("CAD_SYSTEM",          2),   # IFC BIM
    "rhino3dm":        ("CAD_SYSTEM",          2),   # Rhino 3D
    "opencascade":     ("CAD_SYSTEM",          2),   # OpenCASCADE
    "occ":             ("CAD_SYSTEM",          2),   # OpenCASCADE Python
    "FreeCAD":         ("CAD_SYSTEM",          2),
    "freecad":         ("CAD_SYSTEM",          2),

    # Aerospace / Simulation / FEA
    "openmdao":        ("SIMULATION_TOOL",     2),   # NASA OpenMDAO
    "pynastran":       ("SIMULATION_TOOL",     2),   # Nastran FEA
    "pyansys":         ("SIMULATION_TOOL",     2),   # ANSYS
    "fenics":          ("SIMULATION_TOOL",     2),   # FEM solver
    "dolfinx":         ("SIMULATION_TOOL",     2),   # FEM solver
    "simpy":           ("SIMULATION_TOOL",     2),   # discrete simulation
    "su2":             ("SIMULATION_TOOL",     2),   # Stanford CFD
    "gmsh":            ("SIMULATION_TOOL",     2),   # mesh generation
    "scipy":           ("SIMULATION_TOOL",     1),   # weak signal

    # Blockchain / Web3
    "web3":            ("BLOCKCHAIN_NODE",     2),
    "eth_account":     ("BLOCKCHAIN_NODE",     2),
    "eth-account":     ("BLOCKCHAIN_NODE",     2),
    "py_evm":          ("BLOCKCHAIN_NODE",     2),
    "py-evm":          ("BLOCKCHAIN_NODE",     2),
    "brownie":         ("BLOCKCHAIN_NODE",     2),
    "ape":             ("BLOCKCHAIN_NODE",     2),
    "vyper":           ("BLOCKCHAIN_NODE",     2),
    "solana":          ("BLOCKCHAIN_NODE",     3),   # weight=3 overrides web3
    "solders":         ("BLOCKCHAIN_NODE",     3),
    "anchorpy":        ("BLOCKCHAIN_NODE",     3),
    "bitcoin":         ("BLOCKCHAIN_NODE",     2),
    "bitcoinlib":      ("BLOCKCHAIN_NODE",     2),

    # Medical / Healthcare
    "pydicom":         ("MEDICAL_SYSTEM",      2),   # DICOM imaging
    "hl7":             ("MEDICAL_SYSTEM",      2),   # HL7 messaging
    "hl7apy":          ("MEDICAL_SYSTEM",      2),
    "fhir":            ("MEDICAL_SYSTEM",      2),   # FHIR standard
    "fhirclient":      ("MEDICAL_SYSTEM",      2),
    "pymedtermino":    ("MEDICAL_SYSTEM",      2),
    "medspacy":        ("MEDICAL_SYSTEM",      2),
    "nibabel":         ("MEDICAL_SYSTEM",      2),   # neuroimaging
    "nilearn":         ("MEDICAL_SYSTEM",      2),
    "mne":             ("MEDICAL_SYSTEM",      2),   # EEG/MEG

    # Quantum Computing
    "qiskit":          ("QUANTUM_COMPUTING",   2),   # IBM Qiskit
    "pennylane":       ("QUANTUM_COMPUTING",   2),   # Xanadu PennyLane
    "cirq":            ("QUANTUM_COMPUTING",   2),   # Google Cirq
    "braket":          ("QUANTUM_COMPUTING",   2),   # AWS Braket
    "pyquil":          ("QUANTUM_COMPUTING",   2),   # Rigetti PyQuil
    "qutip":           ("QUANTUM_COMPUTING",   2),   # QuTiP
    "strawberryfields":("QUANTUM_COMPUTING",   2),

    # GIS / Geospatial
    "geopandas":       ("GIS_SYSTEM",          2),
    "shapely":         ("GIS_SYSTEM",          2),
    "fiona":           ("GIS_SYSTEM",          2),
    "pyproj":          ("GIS_SYSTEM",          2),
    "rasterio":        ("GIS_SYSTEM",          2),
    "gdal":            ("GIS_SYSTEM",          2),
    "folium":          ("GIS_SYSTEM",          2),
    "cartopy":         ("GIS_SYSTEM",          2),
    "pyqgis":          ("GIS_SYSTEM",          2),   # QGIS Python
    "arcpy":           ("GIS_SYSTEM",          2),   # ArcGIS Python
    "geopy":           ("GIS_SYSTEM",          1),

    # Finance / Trading / Quant
    "quantlib":        ("FINANCE_SYSTEM",      2),
    "backtrader":      ("FINANCE_SYSTEM",      2),
    "zipline":         ("FINANCE_SYSTEM",      2),
    "ccxt":            ("FINANCE_SYSTEM",      2),
    "pyfolio":         ("FINANCE_SYSTEM",      2),
    "alphalens":       ("FINANCE_SYSTEM",      2),
    "bt":              ("FINANCE_SYSTEM",      2),
    "ta":              ("FINANCE_SYSTEM",      1),
    "ta_lib":          ("FINANCE_SYSTEM",      2),
    "ta-lib":          ("FINANCE_SYSTEM",      2),
    "yfinance":        ("FINANCE_SYSTEM",      1),
    "pandas_datareader":("FINANCE_SYSTEM",     2),
    "riskfolio":       ("FINANCE_SYSTEM",      2),
    "ffn":             ("FINANCE_SYSTEM",      2),

    # Game Engine
    "pygame":          ("GAME_ENGINE",         2),
    "panda3d":         ("GAME_ENGINE",         2),
    "arcade":          ("GAME_ENGINE",         2),
    "pyglet":          ("GAME_ENGINE",         2),
    "pyopengl":        ("GAME_ENGINE",         1),
    "godot":           ("GAME_ENGINE",         2),

    # Embedded / IoT
    "micropython":     ("EMBEDDED_SYSTEM",     4),
    "circuitpython":   ("EMBEDDED_SYSTEM",     5),   # weight=5 beats all CLI/ML signals
    "rpi_gpio":        ("EMBEDDED_SYSTEM",     3),
    "rpi-gpio":        ("EMBEDDED_SYSTEM",     3),
    "RPi.GPIO":        ("EMBEDDED_SYSTEM",     3),
    "smbus":           ("EMBEDDED_SYSTEM",     1),
    "smbus2":          ("EMBEDDED_SYSTEM",     3),
    "pyserial":        ("EMBEDDED_SYSTEM",     1),
    "adafruit_blinka": ("EMBEDDED_SYSTEM",     5),
    "machine":         ("EMBEDDED_SYSTEM",     3),   # MicroPython machine
    "wiringpi":        ("EMBEDDED_SYSTEM",     3),

    # Cybersecurity
    "scapy":           ("SECURITY_TOOL",       2),
    "pwntools":        ("SECURITY_TOOL",       2),
    "impacket":        ("SECURITY_TOOL",       2),
    "volatility":      ("SECURITY_TOOL",       2),
    "yara":            ("SECURITY_TOOL",       2),
    "yara_python":     ("SECURITY_TOOL",       2),
    "frida":           ("SECURITY_TOOL",       2),
    "angr":            ("SECURITY_TOOL",       2),
    "cryptography":    ("SECURITY_TOOL",       1),

    # Robotics
    "rospy":           ("ROBOTICS_SYSTEM",     2),   # ROS Python
    "rclpy":           ("ROBOTICS_SYSTEM",     2),   # ROS2 Python
    "moveit":          ("ROBOTICS_SYSTEM",     2),
    "pyrobosim":       ("ROBOTICS_SYSTEM",     2),
    "robotframework":  ("ROBOTICS_SYSTEM",     2),
    "pydrake":         ("ROBOTICS_SYSTEM",     2),   # MIT Drake

    # Scientific Computing / Research
    "astropy":         ("SCIENTIFIC_COMPUTING",2),   # astronomy
    "biopython":       ("SCIENTIFIC_COMPUTING",2),   # bioinformatics
    "rdkit":           ("SCIENTIFIC_COMPUTING",2),   # chemistry
    "openmm":          ("SCIENTIFIC_COMPUTING",2),   # molecular simulation
    "mdanalysis":      ("SCIENTIFIC_COMPUTING",2),   # molecular dynamics
    "sunpy":           ("SCIENTIFIC_COMPUTING",2),   # solar physics
    "obspy":           ("SCIENTIFIC_COMPUTING",2),   # seismology
    "pymatgen":        ("SCIENTIFIC_COMPUTING",2),   # materials science
    "ase":             ("SCIENTIFIC_COMPUTING",2),   # atomic simulation
    "pyiron":          ("SCIENTIFIC_COMPUTING",2),   # materials simulation
    "openbabel":       ("SCIENTIFIC_COMPUTING",2),   # chemistry

    # NLP / Natural Language Processing
    "spacy":           ("NLP_TOOL",            5),   # weight=5 beats FRONTEND_APPLICATION(4) from docs
    "nltk":            ("NLP_TOOL",            3),
    "gensim":          ("NLP_TOOL",            3),
    "textblob":        ("NLP_TOOL",            3),
    "stanza":          ("NLP_TOOL",            3),
    "flair":           ("NLP_TOOL",            3),
    "speechbrain":     ("AUDIO_PROCESSING",    3),
    "whisper":         ("AUDIO_PROCESSING",    3),
    "openai_whisper":  ("AUDIO_PROCESSING",    3),
    "openai-whisper":  ("AUDIO_PROCESSING",    3),

    # Audio / Speech Processing
    "librosa":         ("AUDIO_PROCESSING",    3),
    "pyaudio":         ("AUDIO_PROCESSING",    3),
    "soundfile":       ("AUDIO_PROCESSING",    3),
    "pydub":           ("AUDIO_PROCESSING",    3),
    "pyworld":         ("AUDIO_PROCESSING",    3),
    "espnet":          ("AUDIO_PROCESSING",    3),

    # Computer Vision
    "opencv":          ("COMPUTER_VISION",     3),
    "cv2":             ("COMPUTER_VISION",     3),
    "opencv_python":   ("COMPUTER_VISION",     3),
    "opencv-python":   ("COMPUTER_VISION",     3),
    "opencv_contrib_python": ("COMPUTER_VISION",3),
    "albumentations":  ("COMPUTER_VISION",     3),
    "kornia":          ("COMPUTER_VISION",     3),
    "mmcv":            ("COMPUTER_VISION",     3),
    "detectron2":      ("COMPUTER_VISION",     3),
    "ultralytics":     ("COMPUTER_VISION",     3),   # YOLO

    # Network / Telecom Automation
    "netmiko":         ("NETWORK_TOOL",        2),   # network device SSH
    "napalm":          ("NETWORK_TOOL",        2),   # network device mgmt
    "nornir":          ("NETWORK_TOOL",        2),   # network automation
    "pyshark":         ("NETWORK_TOOL",        2),   # packet capture
    "pynetbox":        ("NETWORK_TOOL",        2),   # NetBox API
    "ncclient":        ("NETWORK_TOOL",        2),   # NETCONF
    "paramiko":        ("NETWORK_TOOL",        1),   # SSH (weak signal)

    # Energy / Power Systems
    "pandapower":      ("ENERGY_SYSTEM",       5),   # weight=5 beats all conflicting signals
    "pypsa":           ("ENERGY_SYSTEM",       5),   # weight=5 beats GRAPH_ANALYTICS(4) from networkx
    "pvlib":           ("ENERGY_SYSTEM",       3),   # solar energy
    "windpowerlib":    ("ENERGY_SYSTEM",       3),   # wind energy
    "pypower":         ("ENERGY_SYSTEM",       3),   # power flow analysis
    "oemof":           ("ENERGY_SYSTEM",       3),   # energy modelling

    # Optimization / Operations Research
    "ortools":         ("OPTIMIZATION_TOOL",   3),   # Google OR-Tools
    "pulp":            ("OPTIMIZATION_TOOL",   3),   # linear programming
    "pyomo":           ("OPTIMIZATION_TOOL",   3),   # algebraic modelling
    "cvxpy":           ("OPTIMIZATION_TOOL",   3),   # convex optimization
    "scipy_optimize":  ("OPTIMIZATION_TOOL",   1),
    "gekko":           ("OPTIMIZATION_TOOL",   3),
    "docplex":         ("OPTIMIZATION_TOOL",   3),   # IBM CPLEX

    # Satellite / Space Systems
    "poliastro":       ("SPACE_SYSTEM",        3),   # orbital mechanics
    "sgp4":            ("SPACE_SYSTEM",        3),   # satellite tracking
    "skyfield":        ("SPACE_SYSTEM",        3),   # astronomy/satellites
    "pyorbital":       ("SPACE_SYSTEM",        3),   # orbital calculations
    "spiceypy":        ("SPACE_SYSTEM",        3),   # NASA SPICE toolkit

    # Document Processing / OCR
    "pdfplumber":      ("DOCUMENT_PROCESSING", 2),
    "pdfminer":        ("DOCUMENT_PROCESSING", 2),
    "pytesseract":     ("DOCUMENT_PROCESSING", 2),   # OCR
    "camelot":         ("DOCUMENT_PROCESSING", 2),   # table extraction
    "docx2txt":        ("DOCUMENT_PROCESSING", 2),
    "textract":        ("DOCUMENT_PROCESSING", 2),
    "pypdf":           ("DOCUMENT_PROCESSING", 2),

    # Graph Analytics / Network Science
    "networkx":        ("GRAPH_ANALYTICS",     4),   # weight=4 overrides DATA_ENGINEERING/MONOREPO
    "igraph":          ("GRAPH_ANALYTICS",     4),
    "graph_tool":      ("GRAPH_ANALYTICS",     3),
    "py2neo":          ("GRAPH_ANALYTICS",     3),   # Neo4j
    "stellargraph":    ("GRAPH_ANALYTICS",     3),

    # Agriculture / Environment
    "geemap":          ("ENVIRONMENTAL",       2),   # Google Earth Engine
    "eemont":          ("ENVIRONMENTAL",       2),
    "pyeto":           ("ENVIRONMENTAL",       2),   # evapotranspiration
    "agepy":           ("ENVIRONMENTAL",       2),
    "plantcv":         ("ENVIRONMENTAL",       2),   # plant phenotyping

    # Supply Chain / Logistics
    "mesa":            ("SIMULATION_TOOL",     2),   # agent-based modelling

    # FPGA / Hardware Description
    "cocotb":          ("FPGA_HARDWARE",       3),   # hardware verification
    "amaranth":        ("FPGA_HARDWARE",       3),   # HDL in Python
    "myhdl":           ("FPGA_HARDWARE",       3),   # HDL in Python
    "migen":           ("FPGA_HARDWARE",       3),   # FPGA toolbox
    "nmigen":          ("FPGA_HARDWARE",       3),
    "litex":           ("FPGA_HARDWARE",       3),   # SoC builder

    # Firmware / RTOS
    "west":            ("FIRMWARE",            3),   # Zephyr build tool
    "zephyr":          ("FIRMWARE",            3),
    "platformio":      ("FIRMWARE",            3),

    # DSP / Software Defined Radio
    "gnuradio":        ("DSP_TOOL",            4),
    "pysdr":           ("DSP_TOOL",            3),
    "rtlsdr":          ("DSP_TOOL",            3),
    "pyrtlsdr":        ("DSP_TOOL",            3),

    # Mobile Application
    "kivy":            ("MOBILE_APPLICATION",  4),
    "kivymd":          ("MOBILE_APPLICATION",  3),
    "buildozer":       ("MOBILE_APPLICATION",  3),
    "flet":            ("MOBILE_APPLICATION",  3),
    "beeware":         ("MOBILE_APPLICATION",  3),
    "toga":            ("MOBILE_APPLICATION",  3),

    # Cloud Infrastructure / IaC
    "pulumi":          ("CLOUD_INFRASTRUCTURE",3),
    "troposphere":     ("CLOUD_INFRASTRUCTURE",3),   # AWS CloudFormation
    "cdktf":           ("CLOUD_INFRASTRUCTURE",3),   # Terraform CDK
    "aws_cdk":         ("CLOUD_INFRASTRUCTURE",3),
    "aws-cdk":         ("CLOUD_INFRASTRUCTURE",3),
    "boto3":           ("CLOUD_INFRASTRUCTURE",1),   # weak signal

    # Container Orchestration
    "kubernetes":      ("CONTAINER_ORCHESTRATION",4),
    "kopf":            ("CONTAINER_ORCHESTRATION",3),  # k8s operators
    "pykube":          ("CONTAINER_ORCHESTRATION",3),
    "helm":            ("CONTAINER_ORCHESTRATION",2),

    # CI/CD Pipeline
    "jenkins":         ("CI_CD_PIPELINE",      3),
    "python_jenkins":  ("CI_CD_PIPELINE",      3),
    "gitlab":          ("CI_CD_PIPELINE",      2),
    "python_gitlab":   ("CI_CD_PIPELINE",      3),
    "jenkinsapi":      ("CI_CD_PIPELINE",      4),

    # Media Streaming
    "ffmpeg_python":   ("MEDIA_STREAMING",     4),
    "ffmpeg-python":   ("MEDIA_STREAMING",     4),
    "gstreamer":       ("MEDIA_STREAMING",     3),
    "pygst":           ("MEDIA_STREAMING",     3),
    "av":              ("MEDIA_STREAMING",     2),   # PyAV
    "ffpyplayer":      ("MEDIA_STREAMING",     2),

    # Automotive / Drone / UAV
    "dronekit":        ("DRONE_UAV",           3),
    "pymavlink":       ("DRONE_UAV",           3),
    "mavsdk":          ("DRONE_UAV",           3),
    "ardupilot":       ("DRONE_UAV",           3),

    # Climate Science
    "xarray":          ("CLIMATE_SCIENCE",     2),
    "metpy":           ("CLIMATE_SCIENCE",     4),
    "iris":            ("CLIMATE_SCIENCE",     2),
    "cftime":          ("CLIMATE_SCIENCE",     2),
    "esmpy":           ("CLIMATE_SCIENCE",     3),
}

IMPORT_SIGNATURES: dict[str, tuple[str, int]] = {
    "django":                ("WEB_APPLICATION",    2),
    "flask":                 ("WEB_APPLICATION",    2),
    "fastapi":               ("API_SERVICE",        2),
    "click":                 ("CLI_TOOL",           2),
    "typer":                 ("CLI_TOOL",           2),
    "torch":                 ("ML_PIPELINE",        2),
    "tensorflow":            ("ML_PIPELINE",        2),
    "keras":                 ("ML_PIPELINE",        2),
    "transformers":          ("ML_PIPELINE",        4),   # weight=4 dominates NLP/CV/AUDIO specialist signals
    "sklearn":               ("ML_PIPELINE",        2),
    "pandas":                ("DATA_ENGINEERING",   1),
    "pyspark":               ("DATA_ENGINEERING",   2),
    "airflow":               ("DATA_ENGINEERING",   2),
    "ansible":               ("DEVOPS_TOOLING",     2),
    "sentence_transformers": ("CODE_GOVERNANCE",    2),
    # Frontend
    "react":              ("FRONTEND_APPLICATION", 2),
    "vue":                ("FRONTEND_APPLICATION", 2),
    "angular":            ("FRONTEND_APPLICATION", 2),
    "svelte":             ("FRONTEND_APPLICATION", 2),

    # CAD
    "ezdxf":              ("CAD_SYSTEM",          2),
    "ifcopenshell":       ("CAD_SYSTEM",          2),
    "FreeCAD":            ("CAD_SYSTEM",          2),

    # Simulation
    "openmdao":           ("SIMULATION_TOOL",     2),
    "pynastran":          ("SIMULATION_TOOL",     2),

    # Blockchain
    "web3":               ("BLOCKCHAIN_NODE",     2),
    "solana":             ("BLOCKCHAIN_NODE",     2),
    "brownie":            ("BLOCKCHAIN_NODE",     2),

    # Medical
    "pydicom":            ("MEDICAL_SYSTEM",      2),
    "hl7":                ("MEDICAL_SYSTEM",      2),
    "nibabel":            ("MEDICAL_SYSTEM",      2),

    # Quantum
    "qiskit":             ("QUANTUM_COMPUTING",   2),
    "pennylane":          ("QUANTUM_COMPUTING",   2),
    "cirq":               ("QUANTUM_COMPUTING",   2),

    # GIS
    "geopandas":          ("GIS_SYSTEM",          2),
    "shapely":            ("GIS_SYSTEM",          2),
    "rasterio":           ("GIS_SYSTEM",          2),
    "fiona":              ("GIS_SYSTEM",          2),
    "pyproj":             ("GIS_SYSTEM",          2),

    # Finance
    "quantlib":           ("FINANCE_SYSTEM",      2),
    "backtrader":         ("FINANCE_SYSTEM",      2),
    "zipline":            ("FINANCE_SYSTEM",      2),
    "ccxt":               ("FINANCE_SYSTEM",      2),

    # Robotics
    "rospy":              ("ROBOTICS_SYSTEM",     2),
    "rclpy":              ("ROBOTICS_SYSTEM",     2),

    # Scientific
    "astropy":            ("SCIENTIFIC_COMPUTING",2),
    "biopython":          ("SCIENTIFIC_COMPUTING",2),
    "rdkit":              ("SCIENTIFIC_COMPUTING",2),

    # Security
    "scapy":              ("SECURITY_TOOL",       2),
    "pwntools":           ("SECURITY_TOOL",       2),
}

# ------------------------------------------------------------------ #
# Universal Language Extensions                                        #
# ------------------------------------------------------------------ #

LANGUAGE_EXTENSIONS: dict[str, str] = {
    # Python
    ".py":      "Python",
    ".pyw":     "Python",
    ".pyx":     "Cython",
    ".pxd":     "Cython",
    # JavaScript / TypeScript
    ".js":      "JavaScript",
    ".jsx":     "JavaScript",
    ".mjs":     "JavaScript",
    ".cjs":     "JavaScript",
    ".ts":      "TypeScript",
    ".tsx":     "TypeScript",
    # JVM
    ".java":    "Java",
    ".kt":      "Kotlin",
    ".kts":     "Kotlin",
    ".scala":   "Scala",
    ".groovy":  "Groovy",
    ".clj":     "Clojure",
    # C family
    ".c":       "C",
    ".h":       "C",
    ".cpp":     "C++",
    ".cc":      "C++",
    ".cxx":     "C++",
    ".hpp":     "C++",
    ".hxx":     "C++",
    ".h++":     "C++",
    # C# / .NET
    ".cs":      "C#",
    ".vb":      "Visual Basic",
    ".fs":      "F#",
    ".fsx":     "F#",
    # Systems
    ".rs":      "Rust",
    ".go":      "Go",
    ".zig":     "Zig",
    ".d":       "D",
    # Mobile
    ".swift":   "Swift",
    ".m":       "Objective-C",
    ".mm":      "Objective-C",
    ".dart":    "Dart",
    ".kt":      "Kotlin",
    # Scripting
    ".rb":      "Ruby",
    ".php":     "PHP",
    ".pl":      "Perl",
    ".pm":      "Perl",
    ".lua":     "Lua",
    ".tcl":     "Tcl",
    # Shell
    ".sh":      "Shell",
    ".bash":    "Shell",
    ".zsh":     "Shell",
    ".fish":    "Shell",
    ".ps1":     "PowerShell",
    ".psm1":    "PowerShell",
    # Functional
    ".hs":      "Haskell",
    ".lhs":     "Haskell",
    ".ex":      "Elixir",
    ".exs":     "Elixir",
    ".erl":     "Erlang",
    ".hrl":     "Erlang",
    ".ml":      "OCaml",
    ".mli":     "OCaml",
    # Scientific
    ".r":       "R",
    ".R":       "R",
    ".jl":      "Julia",
    ".f90":     "Fortran",
    ".f95":     "Fortran",
    ".f03":     "Fortran",
    ".for":     "Fortran",
    ".f":       "Fortran",
    ".mat":     "MATLAB",
    # Assembly
    ".asm":     "Assembly",
    ".s":       "Assembly",
    ".S":       "Assembly",
    # Ada
    ".ada":     "Ada",
    ".adb":     "Ada",
    ".ads":     "Ada",
    # COBOL
    ".cob":     "COBOL",
    ".cbl":     "COBOL",
    ".cobol":   "COBOL",
    # Web
    ".html":    "HTML",
    ".htm":     "HTML",
    ".css":     "CSS",
    ".scss":    "SCSS",
    ".sass":    "SASS",
    ".less":    "LESS",
    ".vue":     "Vue",
    ".svelte":  "Svelte",
    # Data / Config
    ".sql":     "SQL",
    ".yaml":    "YAML",
    ".yml":     "YAML",
    ".toml":    "TOML",
    ".xml":     "XML",
    # Infrastructure
    ".tf":      "Terraform",
    ".hcl":     "HCL",
    # Interface Definition
    ".proto":   "Protobuf",
    ".thrift":  "Thrift",
    ".graphql": "GraphQL",
    ".gql":     "GraphQL",
    ".wsdl":    "WSDL",
    ".idl":     "IDL",
    # Docs
    # Notebooks
    # Other
    ".vim":     "VimScript",
    ".el":      "Emacs Lisp",
    ".nix":     "Nix",
    ".dhall":   "Dhall",
    ".ipynb":   "Jupyter Notebook",
}

# ------------------------------------------------------------------ #
# Build System Detection                                               #
# ------------------------------------------------------------------ #

# Maps filename → build system name
BUILD_SYSTEM_FILE_NAMES: dict[str, str] = {
    # C / C++
    "CMakeLists.txt":      "CMake",
    "Makefile":            "Make",
    "makefile":            "Make",
    "GNUmakefile":         "Make",
    "meson.build":         "Meson",
    "SConstruct":          "SCons",
    "BUILD":               "Bazel",
    "BUILD.bazel":         "Bazel",
    "WORKSPACE":           "Bazel",
    "WORKSPACE.bazel":     "Bazel",
    # Java / JVM
    "pom.xml":             "Maven",
    "build.gradle":        "Gradle",
    "build.gradle.kts":    "Gradle",
    "settings.gradle":     "Gradle",
    "settings.gradle.kts": "Gradle",
    "build.xml":           "Ant",
    # Python
    "setup.py":            "Setuptools",
    "setup.cfg":           "Setuptools",
    "pyproject.toml":      "Python Build",
    # Rust
    "Cargo.toml":          "Cargo",
    # Go
    "go.mod":              "Go Modules",
    # JavaScript
    "package.json":        "NPM",
    "yarn.lock":           "Yarn",
    "pnpm-lock.yaml":      "PNPM",
    # Ruby
    "Gemfile":             "Bundler",
    "Rakefile":            "Rake",
    # PHP
    "composer.json":       "Composer",
    # .NET
    "*.csproj":            "MSBuild",
    "*.sln":               "MSBuild",
    "*.vbproj":            "MSBuild",
    # Swift
    "Package.swift":       "Swift Package Manager",
    # Haskell
    "stack.yaml":          "Stack",
    "*.cabal":             "Cabal",
    # Erlang / Elixir
    "rebar.config":        "Rebar3",
    "mix.exs":             "Mix",
    # Scala
    "build.sbt":           "SBT",
    # Conda / Python env
    "environment.yml":     "Conda",
    "environment.yaml":    "Conda",
    "conda.yml":           "Conda",
    "conda.yaml":          "Conda",
    # Nix
    "default.nix":         "Nix",
    "flake.nix":           "Nix",
    # Lua
    "rockspec":            "LuaRocks",
}

# Extension-based build system detection
BUILD_SYSTEM_EXTENSIONS: dict[str, str] = {
    ".cmake":   "CMake",
    ".gradle":  "Gradle",
    ".cabal":   "Cabal",
}

# ------------------------------------------------------------------ #
# Document File Extensions (non-executable)                            #
# ------------------------------------------------------------------ #
# Goes into detected_file_types, NOT detected_languages

DOCUMENT_FILE_EXTENSIONS: dict[str, str] = {
    ".pdf":     "PDF Document",
    ".doc":     "Word Document",
    ".docx":    "Word Document",
    ".xls":     "Excel Spreadsheet",
    ".xlsx":    "Excel Spreadsheet",
    ".ppt":     "PowerPoint",
    ".pptx":    "PowerPoint",
    ".tsv":     "TSV",
    ".md":      "Markdown",
    ".rst":     "ReStructuredText",
    ".txt":     "Text",
    ".adoc":    "AsciiDoc",
    ".tex":     "LaTeX",
    ".json":    "JSON",
    ".yaml":    "YAML",
    ".yml":     "YAML",
    ".xml":     "XML",
    ".toml":    "TOML",
    ".hcl":     "HCL",
    ".conf":       "Configuration File",
    ".ini":        "Configuration File",
    ".cfg":        "Configuration File",
    ".bat":        "Windows Batch Script",
    ".properties": "Properties File",
    ".hbs":        "Handlebars Template",
    ".mdx":        "MDX",
    ".po":         "Gettext Translation",
    ".mo":         "Gettext Binary",
    ".m4":         "M4 Macro",
    ".bak":        "Backup File",
    ".tmp":     "Temporary File",
    ".log":     "Log File",
    ".out":     "Output File",
    # Microsoft Office
    ".accdb": "Microsoft Access Database",
    ".mdb":   "Microsoft Access Database",
    ".xls":   "Excel Spreadsheet",
    ".ppt":   "PowerPoint",
    ".doc":   "Word Document",
    # SQL Server
    ".mdf":   "SQL Server Data File",
    ".ldf":   "SQL Server Log File",
    ".ndf":   "SQL Server Secondary Data File",
    ".bak":   "SQL Server Backup",
    
}

# ------------------------------------------------------------------ #
# Model File Extensions (ML / Neural Network weights)                  #
# ------------------------------------------------------------------ #
# Goes into detected_model_files — never passed to AST parser
# Module 2 must SKIP these — binary blobs, not source code

MODEL_FILE_EXTENSIONS: dict[str, str] = {
    # PyTorch
    ".pt":          "PyTorch Model",
    ".pth":         "PyTorch Model",
    # HuggingFace
    ".bin":         "Model Binary",
    ".safetensors": "SafeTensors Model",
    # llama.cpp / GGML
    ".gguf":        "GGUF Model",
    ".ggml":        "GGML Model",
    # TensorFlow / Keras
    ".ckpt":        "Checkpoint Model",
    ".h5":          "Keras Model",
    ".pb":          "TensorFlow Model",
    ".tflite":      "TensorFlow Lite",
    # ONNX — universal exchange format
    ".onnx":        "ONNX Model",
    # Apple
    ".mlmodel":     "CoreML Model",
    ".mlpackage":   "CoreML Model",
    # scikit-learn / joblib
    ".pkl":         "Pickle Model",
    ".joblib":      "Joblib Model",
    # NumPy weights / embeddings
    ".npy":         "NumPy Array",  # may be data OR model weights
    ".npz":         "NumPy Archive",
    # Darknet / YOLO
    ".weights":     "Model Weights",
    # Caffe
    ".caffemodel":  "Caffe Model",
    ".prototxt":    "Caffe Config",
    # MXNet
    ".params":      "MXNet Model",
    # PaddlePaddle
    ".pdparams":    "PaddlePaddle Model",
    ".pdmodel":     "PaddlePaddle Model",
    # Theano
    ".nnet":        "Neural Network Model",
    # TensorRT
    ".engine":      "TensorRT Engine",
    ".trt":         "TensorRT Engine",
    # OpenVINO — xml alone too common, skip
    # ".xml":       "OpenVINO Model",  # disabled — too many false positives
    ".bin":         "OpenVINO Weights",   # already covered above
}

# ------------------------------------------------------------------ #
# ERP System Package Signatures                                        #
# ------------------------------------------------------------------ #
# Add new ERP connectors here — no engine changes required.
# Pattern: "package_name": ("ERP_SYSTEM", weight)

ERP_PACKAGE_SIGNATURES: dict[str, tuple[str, int]] = {
    # SAP
    "pyrfc":                  ("ERP_SYSTEM", 2),
    "pynwrfc":                ("ERP_SYSTEM", 2),
    "python_sapnwrfc":        ("ERP_SYSTEM", 2),
    "hdbcli":                 ("ERP_SYSTEM", 2),   # SAP HANA
    "sapnwrfc":               ("ERP_SYSTEM", 2),

    # Oracle ERP / EBS
    "cx_oracle":              ("ERP_SYSTEM", 2),
    "cx-oracle":              ("ERP_SYSTEM", 2),
    "oracledb":               ("ERP_SYSTEM", 2),

    # Salesforce
    "simple_salesforce":      ("ERP_SYSTEM", 2),
    "salesforce_bulk":        ("ERP_SYSTEM", 1),
    "pysftp":                 ("ERP_SYSTEM", 1),

    # Microsoft Dynamics
    "msal":                   ("ERP_SYSTEM", 1),   # weak — needs corroboration
    "dynamics365":            ("ERP_SYSTEM", 2),

    # NetSuite
    "netsuite":               ("ERP_SYSTEM", 2),
    "netsuite_sdk":           ("ERP_SYSTEM", 2),

    # PeopleSoft
    "peoplesoft":             ("ERP_SYSTEM", 2),

    # Workday
    "workday":                ("ERP_SYSTEM", 2),

    # ServiceNow
    "pysnow":                 ("ERP_SYSTEM", 2),
    "servicenow":             ("ERP_SYSTEM", 2),

    # Infor
    "infor_sdk":              ("ERP_SYSTEM", 2),

    # Sage
    "sage_api":               ("ERP_SYSTEM", 2),

    # Epicor
    "epicor":                 ("ERP_SYSTEM", 2),

    # IFS
    "ifs_connect":            ("ERP_SYSTEM", 2),

    # Generic ERP signals
    "odoo":                   ("ERP_SYSTEM", 2),
    "openerp":                ("ERP_SYSTEM", 2),
}

# ------------------------------------------------------------------ #
# Content-Based Application Pattern Detection                          #
# ------------------------------------------------------------------ #
# For projects that ARE the product (Redis, Rust, Odoo source repos)
# Detected by scanning internal file content patterns
# Used in _detect_from_internal_patterns() in cognition_engine.py

CONTENT_PATTERN_SIGNATURES: list[dict] = [
    # Redis — detected by src/server.c or redis.conf content
    {
        "name": "Redis",
        "app_type": "DATABASE_SYSTEM",
        "weight": 2,
        "file_patterns": ["redis.conf", "src/server.c", "src/redis.h"],
        "content_keywords": ["redis_server", "redisServer", "REDIS_VERSION"],
    },
    # Rust compiler — detected by Cargo.toml workspace with compiler members
    {
        "name": "Rust Compiler",
        "app_type": "COMPILER_TOOLCHAIN",
        "weight": 2,
        "file_patterns": ["Cargo.toml", "compiler/rustc/Cargo.toml",
                          "src/rustc/lib.rs", "compiler/rustc/src/main.rs"],
        "content_keywords": ["rustc", "rustdoc", "rust-lang", "compiler/rustc",
                             "rustc_middle", "rustc_driver", "rustc_interface"],
    },
    # Go compiler — detected by src/cmd/go/main.go or GOROOT structure
    {
        "name": "Go Compiler",
        "app_type": "COMPILER_TOOLCHAIN",
        "weight": 2,
        "file_patterns": ["src/cmd/go/main.go", "src/runtime/runtime.go",
                          "src/cmd/compile/main.go", "src/builtin/builtin.go"],
        "content_keywords": ["GOROOT", "go/src", "cmd/compile",
                             "runtime.main", "go tool", "go command"],
    },
    # Odoo ERP — odoo-bin is a unique file that exists ONLY in Odoo repositories
    # File existence alone is sufficient — no content keyword needed
    # weight=3 overrides DATABASE_SYSTEM(2) from psycopg2 in requirements.txt
    {
        "name": "Odoo",
        "app_type": "ERP_SYSTEM",
        "weight": 3,
        "file_patterns": ["odoo-bin"],
        "content_keywords": [],    # empty = file existence alone is the signal
    },
    # Odoo fallback — detected by setup.py with name=odoo
    {
        "name": "Odoo (setup.py)",
        "app_type": "ERP_SYSTEM",
        "weight": 3,
        "file_patterns": ["setup.py"],
        "content_keywords": ["lib_name = 'odoo'", "name = 'odoo'", "name='odoo'",
                             "openerp"],
    },
    # spaCy — detected by spacy/about.py or spacy/__init__.py
    # spaCy repo has many React package.json files in docs → FRONTEND dominates
    # Content pattern overrides package scoring
    {
        "name": "spaCy",
        "app_type": "NLP_TOOL",
        "weight": 15,
        "file_patterns": ["spacy/about.py", "spacy/__init__.py",
                          "spacy/language.py"],
        "content_keywords": ["spacy", "__version__", "Language", "nlp"],
    },
    # NLTK — detected by nltk/__init__.py
    {
        "name": "NLTK",
        "app_type": "NLP_TOOL",
        "weight": 15,
        "file_patterns": ["nltk/__init__.py", "nltk/corpus/__init__.py"],
        "content_keywords": ["nltk", "Natural Language", "corpus", "tokenize"],
    },
    # hl7apy — detected by hl7apy/__init__.py
    {
        "name": "hl7apy",
        "app_type": "MEDICAL_SYSTEM",
        "weight": 15,
        "file_patterns": ["hl7apy/__init__.py", "hl7apy/core/__init__.py",
                          "hl7apy/core.py"],
        "content_keywords": [],
    },
    # librosa — detected by librosa/__init__.py
    {
        "name": "librosa",
        "app_type": "AUDIO_PROCESSING",
        "weight": 15,
        "file_patterns": ["librosa/__init__.py", "librosa/core/__init__.py"],
        "content_keywords": ["librosa", "audio", "stft", "mel_spectrogram"],
    },
    # Whisper — detected by whisper/__init__.py
    # weight=30 guarantees AUDIO_PROCESSING dominates any ML signals
    {
        "name": "Whisper",
        "app_type": "AUDIO_PROCESSING",
        "weight": 30,
        "file_patterns": ["whisper/__init__.py", "whisper/model.py"],
        "content_keywords": [],
    },
    # opencv-python — file existence alone sufficient
    {
        "name": "OpenCV",
        "app_type": "COMPUTER_VISION",
        "weight": 15,
        "file_patterns": ["cv2/__init__.py", "cv2/cv2.pyi",
                          "cv2/__init__.pyi"],
        "content_keywords": [],
    },
    # python-igraph — detected by igraph/__init__.py
    {
        "name": "python-igraph",
        "app_type": "GRAPH_ANALYTICS",
        "weight": 15,
        "file_patterns": ["igraph/__init__.py", "igraph/Graph.py",
                          "src/igraph/__init__.py"],
        "content_keywords": ["igraph", "Graph", "Vertex", "Edge"],
    },
    # Ultralytics — weight=30 guarantees CV dominates GIS/ML signals
    {
        "name": "Ultralytics/YOLO",
        "app_type": "COMPUTER_VISION",
        "weight": 30,
        "file_patterns": ["ultralytics/__init__.py",
                          "ultralytics/models/yolo/__init__.py"],
        "content_keywords": [],
    },
    # OpenMDAO — detected by openmdao/__init__.py
    {
        "name": "OpenMDAO",
        "app_type": "SIMULATION_TOOL",
        "weight": 15,
        "file_patterns": ["openmdao/__init__.py",
                          "openmdao/core/problem.py"],
        "content_keywords": [],
    },
    # Drake (MIT Robotics) — detected by drake/__init__.py or CMakeLists
    {
        "name": "Drake",
        "app_type": "ROBOTICS_SYSTEM",
        "weight": 15,
        "file_patterns": ["drake/__init__.py", "drake/multibody/__init__.py",
                          "bindings/pydrake/__init__.py",
                          "CMakeLists.txt"],
        "content_keywords": ["drake", "pydrake", "MultibodyPlant",
                             "RigidBody", "DiagramBuilder"],
    },
    # pwntools — detected by pwn/__init__.py or pwnlib/__init__.py
    {
        "name": "pwntools",
        "app_type": "SECURITY_TOOL",
        "weight": 15,
        "file_patterns": ["pwnlib/__init__.py", "pwn/__init__.py",
                          "pwnlib/exploit.py", "pwnlib/tubes/__init__.py"],
        "content_keywords": [],
    },
    # U-Boot — detected by common/board_f.c or u-boot source layout
    {
        "name": "U-Boot",
        "app_type": "FIRMWARE",
        "weight": 15,
        "file_patterns": ["common/board_f.c", "common/board_r.c",
                          "include/configs", "arch/arm/lib/crt0.S",
                          "tools/mkimage.c"],
        "content_keywords": [],
    },
    # GStreamer Python — detected by gi/overrides/Gst.py or examples
    {
        "name": "gst-python",
        "app_type": "MEDIA_STREAMING",
        "weight": 15,
        "file_patterns": ["gi/overrides/Gst.py", "testsuite/test_gst.py",
                          "examples/python/gst-launch.py",
                          "plugin/python/gstpythonplugin.c"],
        "content_keywords": [],
    },
    # ArduPilot — detected by ArduCopter/ArduCopter.cpp or libraries/AP_*
    {
        "name": "ArduPilot",
        "app_type": "DRONE_UAV",
        "weight": 15,
        "file_patterns": ["ArduCopter/ArduCopter.cpp", "ArduPlane/ArduPlane.cpp",
                          "libraries/AP_HAL/AP_HAL.h",
                          "libraries/AP_Vehicle/AP_Vehicle.h",
                          "Tools/ardupilotwaf/ardupilotwaf.py"],
        "content_keywords": [],
    },
    # GNU Radio — detected by gnuradio-runtime or grc files
    {
        "name": "GNU Radio",
        "app_type": "DSP_TOOL",
        "weight": 15,
        "file_patterns": ["gnuradio-runtime/include/gnuradio/top_block.h",
                          "gr-blocks/include/gnuradio/blocks/api.h",
                          "gnuradio-runtime/python/gnuradio/gr/__init__.py",
                          "CMakeLists.txt"],
        "content_keywords": ["gnuradio", "GNU Radio", "gr::top_block", "gr::hier_block2"],
    },
    # Kivy — detected by kivy/__init__.py or kivy/app.py
    {
        "name": "Kivy",
        "app_type": "MOBILE_APPLICATION",
        "weight": 15,
        "file_patterns": ["kivy/__init__.py", "kivy/app.py",
                          "kivy/uix/widget.py"],
        "content_keywords": [],
    },
    # CircuitPython — file existence alone sufficient
    {
        "name": "CircuitPython",
        "app_type": "EMBEDDED_SYSTEM",
        "weight": 15,
        "file_patterns": ["shared-bindings/__init__.py",
                          "supervisor/main.c",
                          "ports/raspberrypi/main.c",
                          "shared-module/__init__.py",
                          "py/circuitpy_mpconfig.h",
                          "ports/atmel-samd/main.c",
                          "ports/stm/main.c",
                          "CIRCUITPY_ENABLE_FINALIZATION"],
        "content_keywords": [],
    },
    # FreeCAD — detected by src/App/Application.cpp or FreeCAD.h
    {
        "name": "FreeCAD",
        "app_type": "CAD_SYSTEM",
        "weight": 3,
        "file_patterns": ["src/App/Application.cpp", "src/Gui/Application.cpp",
                          "src/Base/Console.h", "cMake/FindFreeCAD.cmake"],
        "content_keywords": ["FreeCAD", "App::Application", "Gui::Application",
                             "FreeCADGui", "freecad"],
    },
    # LibreCAD — detected by src/lib/libdxfrw
    {
        "name": "LibreCAD",
        "app_type": "CAD_SYSTEM",
        "weight": 3,
        "file_patterns": ["src/lib/libdxfrw/libdxfrw.h", "src/main.cpp",
                          "librecad.pro"],
        "content_keywords": ["LibreCAD", "libdxfrw", "RS_EntityContainer"],
    },
    # Nginx — detected by src/nginx.c or nginx.conf
    {
        "name": "Nginx",
        "app_type": "WEB_SERVER",
        "weight": 2,
        "file_patterns": ["src/core/nginx.h", "conf/nginx.conf"],
        "content_keywords": ["nginx_version", "NGX_", "ngx_module_t"],
    },
    # Linux Kernel
    {
        "name": "Linux Kernel",
        "app_type": "OPERATING_SYSTEM",
        "weight": 2,
        "file_patterns": ["Makefile", "include/linux/kernel.h"],
        "content_keywords": ["LINUX_VERSION_CODE", "linux/kernel.h", "THIS_MODULE"],
    },
    # PostgreSQL
    {
        "name": "PostgreSQL",
        "app_type": "DATABASE_SYSTEM",
        "weight": 2,
        "file_patterns": ["src/backend/main/main.c"],
        "content_keywords": ["PostgreSQL", "postmaster", "pg_config"],
    },
    # MySQL
    {
        "name": "MySQL",
        "app_type": "DATABASE_SYSTEM",
        "weight": 2,
        "file_patterns": ["sql/mysqld.cc"],
        "content_keywords": ["MYSQL_VERSION", "mysqld", "InnoDB"],
    },
]

# ------------------------------------------------------------------ #
# ERP File Extensions                                                  #
# ------------------------------------------------------------------ #
# Add new ERP extensions here — no engine changes required.
# Pattern: ".ext": "ERP Name Language"

ERP_LANGUAGE_EXTENSIONS: dict[str, str] = {
    # SAP ABAP
    ".abap":        "SAP ABAP",
    ".prog":        "SAP ABAP",
    ".fugr":        "SAP ABAP",
    ".clas":        "SAP ABAP",
    ".intf":        "SAP ABAP",
    ".tabl":        "SAP ABAP",
    ".doma":        "SAP ABAP",
    ".dtel":        "SAP ABAP",
    ".msag":        "SAP ABAP",
    ".tran":        "SAP ABAP",

    # Oracle PL/SQL / EBS
    ".pls":         "Oracle PL/SQL",
    ".pks":         "Oracle PL/SQL",
    ".pkb":         "Oracle PL/SQL",
    ".fnc":         "Oracle PL/SQL",
    ".prc":         "Oracle PL/SQL",
    ".trg":         "Oracle PL/SQL",
    ".vw":          "Oracle PL/SQL",
    ".sqr":         "Oracle SQR",
    ".fmb":         "Oracle Forms",
    ".rdf":         "Oracle Reports",

    # Microsoft Dynamics X++
    ".xpp":         "Microsoft Dynamics X++",
    ".axproj":      "Microsoft Dynamics X++",

    # Salesforce
    ".cls":         "Salesforce Apex",
    ".trigger":     "Salesforce Apex",
    ".page":        "Salesforce Visualforce",
    ".component":   "Salesforce Visualforce",
    ".app":         "Salesforce Lightning",
    ".cmp":         "Salesforce Lightning",
    ".evt":         "Salesforce Lightning",
    ".intf":        "Salesforce Lightning",

    # NetSuite SuiteScript
    ".ns":          "NetSuite SuiteScript",
    ".sdf":         "NetSuite SDF",
    ".ssp":         "NetSuite SuiteScript",

    # PeopleSoft
    ".peoplecode":  "PeopleSoft PeopleCode",
    ".pcode":       "PeopleSoft PeopleCode",

    # Odoo / OpenERP
    ".odoo":        "Odoo",

    # IFS
    ".ifs":         "IFS Applications",

    # Maximo (IBM)
    ".maxobj":      "IBM Maximo",
    ".maxml":       "IBM Maximo",

    # CAD / Engineering Design
    ".dwg":         "AutoCAD Drawing",
    ".dxf":         "AutoCAD Exchange",
    ".dwt":         "AutoCAD Template",
    ".rvt":         "Revit Model",
    ".ifc":         "IFC BIM Model",
    ".3dm":         "Rhino 3D Model",
    ".skp":         "SketchUp Model",
    ".sldprt":      "SolidWorks Part",
    ".sldasm":      "SolidWorks Assembly",
    ".slddrw":      "SolidWorks Drawing",
    ".prt":         "PTC Creo Part",
    ".catpart":     "CATIA Part",
    ".catproduct":  "CATIA Assembly",
    ".stp":         "STEP CAD File",
    ".step":        "STEP CAD File",
    ".iges":        "IGES CAD File",
    ".igs":         "IGES CAD File",
    ".stl":         "STL 3D Model",
    ".obj":         "OBJ 3D Model",
    ".3ds":         "3DS Max Model",
    ".fbx":         "FBX 3D Model",

    # Aerospace / Simulation / FEA
    ".nas":         "Nastran Input",
    ".bdf":         "Nastran Bulk Data",
    ".f06":         "Nastran Output",
    ".op2":         "Nastran Binary Output",
    ".inp":         "Abaqus Input",
    ".odb":         "Abaqus Output",
    ".cdb":         "ANSYS Database",
    ".foam":        "OpenFOAM Case",
    ".cgns":        "CFD General Notation",
    ".vtk":         "VTK Visualization",
    ".vtu":         "VTK Unstructured",
    ".su2":         "SU2 Config",

    # Blockchain / Web3
    ".sol":         "Solidity Smart Contract",
    ".vy":          "Vyper Smart Contract",
    ".move":        "Move Smart Contract",
    ".cairo":       "Cairo Smart Contract",
    ".abi":         "ABI Definition",

    # Medical / Healthcare
    ".dcm":         "DICOM Medical Image",
    ".hl7":         "HL7 Medical Record",
    ".nii":         "NIfTI Neuroimaging",
    ".edf":         "EEG Data Format",

    # Quantum Computing
    ".qasm":        "OpenQASM Circuit",
    ".quil":        "Quil Circuit",

    # GIS / Geospatial
    ".shp":         "Shapefile",
    ".kml":         "Google Earth KML",
    ".kmz":         "Google Earth KMZ",
    ".gpkg":        "GeoPackage",
    ".geotiff":     "GeoTIFF",

    # Game Development
    ".tscn":        "Godot Scene",
    ".gd":          "GDScript",
    ".tres":        "Godot Resource",
    ".prefab":      "Unity Prefab",

    # Embedded / IoT
    ".ino":         "Arduino Sketch",
    ".hex":         "Embedded Binary",
    ".elf":         "Embedded ELF",
    ".firmware":    "Firmware Binary",

    # Robotics
    ".urdf":        "Robot Description",
    ".xacro":       "ROS Macro",
    ".bag":         "ROS Bag File",
    ".world":       "Gazebo World",

    # Scientific
    ".fits":        "FITS Astronomy",
    ".nc":          "NetCDF Scientific",
    ".fasta":       "FASTA Sequence",
    ".fastq":       "FASTQ Sequence",
    ".pdb":         "Protein Data Bank",
    ".cif":         "Crystallographic File",

    # Cybersecurity
    ".yar":         "YARA Rule",
    ".yara":        "YARA Rule",
    ".pcap":        "Network Capture",
    ".pcapng":      "Network Capture",

    # Finance
    ".mq4":         "MetaTrader 4 Script",
    ".mq5":         "MetaTrader 5 Script",

    # Audio / Speech
    ".wav":         "Audio File",
    ".mp3":         "Audio File",
    ".flac":        "Audio File",
    ".ogg":         "Audio File",
    ".aiff":        "Audio File",
    ".opus":        "Audio File",

    # Chemistry / Materials Science
    ".mol":         "Molecular Structure",
    ".mol2":        "Molecular Structure",
    ".xyz":         "Atomic Coordinates",
    ".cml":         "Chemical Markup",

    # Satellite / Space
    ".tle":         "Two-Line Element",
    ".sp3":         "GNSS Orbit Data",

    # Network / Telecom
    ".yang":        "YANG Network Model",

    # Graph / Network
    ".graphml":     "GraphML Network",
    ".gexf":        "GEXF Network",
    ".gml":         "GML Network",

    # Optimization
    ".lp":          "Linear Program",
    ".mps":         "Mathematical Program",
    ".mod":         "AMPL Model",

    # FPGA / Hardware Description
    ".vhd":         "VHDL",
    ".vhdl":        "VHDL",
    ".v":           "Verilog",
    ".sv":          "SystemVerilog",
    ".svh":         "SystemVerilog Header",
    ".xdc":         "Xilinx Constraints",

    # PCB / Electronics
    ".kicad_pcb":   "KiCad PCB",
    ".kicad_sch":   "KiCad Schematic",
    ".brd":         "Eagle PCB",
    ".sch":         "Schematic",
    ".gbr":         "Gerber File",

    # Firmware / Device Tree
    ".dts":         "Device Tree Source",
    ".dtsi":        "Device Tree Include",
    ".dtb":         "Device Tree Blob",
    ".kconfig":     "Linux Kconfig",

    # DSP / GNU Radio
    ".grc":         "GNU Radio Companion",

    # Cloud Infrastructure
    ".tf":          "Terraform Config",
    ".tfvars":      "Terraform Variables",
    ".hcl":         "HCL Config",

    # Container Orchestration
    ".helm":        "Helm Chart",

    # CI/CD
    ".jenkinsfile": "Jenkinsfile",

    # Drone / MAVLink
    ".param":       "Drone Parameter File",
    ".waypoints":   "Drone Waypoints",

    # Climate Science
    ".grib":        "GRIB Weather Data",
    ".grib2":       "GRIB2 Weather Data",
}

# ------------------------------------------------------------------ #
# Entry Points                                                         #
# ------------------------------------------------------------------ #

ENTRY_POINT_NAMES: set[str] = {
    "main.py", "app.py", "run.py", "server.py",
    "manage.py",
    "wsgi.py",
    "asgi.py",
    "cli.py",
    "__main__.py",
}

ENTRY_POINT_NOISE_DIRS: set[str] = {
    "backups", "backup", "archive", "archives",
    "tests", "test",
    "migrations",
    "dist", "build",
}

# ------------------------------------------------------------------ #
# Skip Directories                                                     #
# ------------------------------------------------------------------ #

SKIP_DIRECTORIES: set[str] = {
    ".git", ".svn", ".hg",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".tox", ".nox", "htmlcov",
    ".venv", "venv", "env",
    "dist", "build", "eggs", ".eggs", "wheels",
    "node_modules", ".next", ".nuxt", "out",
    "backups", "backup", "archive", "archives",
    "migrations",
    ".idea", ".vscode", ".vs",
    "vendor",
    "target",
}

# ------------------------------------------------------------------ #
# Configuration Files                                                  #
# ------------------------------------------------------------------ #

CONFIG_FILE_NAMES: set[str] = {
    # Python
    ".env", ".env.example", ".env.local", ".env.production",
    ".env.staging", ".env.development", ".env.test",
    "settings.py", "config.py", "config.yaml", "config.yml",
    "pyproject.toml", "setup.cfg", "setup.py",
    "requirements.txt", "Pipfile", "Pipfile.lock",
    "environment.yml", "environment.yaml",
    "conda.yml", "conda.yaml",
    # Infrastructure
    "Dockerfile", "Dockerfile.dev", "Dockerfile.prod",
    "Dockerfile.production", "Dockerfile.staging",
    "docker-compose.yml", "docker-compose.yaml",
    "docker-compose.dev.yml", "docker-compose.prod.yml",
    "docker-compose.override.yml",
    "Vagrantfile", "Jenkinsfile", "Makefile",
    ".github",
    # JavaScript / TypeScript
    "package.json", "package-lock.json", "yarn.lock",
    "tsconfig.json", ".eslintrc.json", ".babelrc",
    "webpack.config.js", "vite.config.ts", "next.config.js",
    # Go
    "go.mod", "go.sum",
    # Rust
    "Cargo.toml", "Cargo.lock",
    # Java / Kotlin
    "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle",
    # C / C++
    "CMakeLists.txt",
    # C# / VB
    ".csproj", ".sln", ".vbproj",
    # Ruby
    "Gemfile", "Gemfile.lock",
    # PHP
    "composer.json", "composer.lock",
    # Cloud / CI
    ".travis.yml", "azure-pipelines.yml", "cloudbuild.yaml",
    "serverless.yml", "netlify.toml", "vercel.json",
    ".gitlab-ci.yml",
    # Swift
    "Package.swift",
    # Elixir
    "mix.exs",
    # Scala
    "build.sbt",
    # Haskell
    "stack.yaml",
    # Nix
    "default.nix", "flake.nix",
    # Lua
    "rockspec",
}

CONFIG_FILE_EXTENSIONS: set[str] = {
    ".cmake", ".gradle", ".csproj", ".sln", ".vbproj",
    ".pbxproj", ".cabal",
}

DOCKERFILE_PREFIXES: set[str] = {"dockerfile"}
ENV_FILE_PREFIXES: set[str] = {".env"}

# ------------------------------------------------------------------ #
# Config → Language Map                                                #
# ------------------------------------------------------------------ #

CONFIG_FILE_LANGUAGE_MAP: dict[str, str] = {
    "package.json":        "JavaScript",
    "package-lock.json":   "JavaScript",
    "yarn.lock":           "JavaScript",
    "tsconfig.json":       "TypeScript",
    "webpack.config.js":   "JavaScript",
    "vite.config.ts":      "TypeScript",
    "next.config.js":      "JavaScript",
    ".eslintrc.json":      "JavaScript",
    ".babelrc":            "JavaScript",
    "go.mod":              "Go",
    "go.sum":              "Go",
    "Cargo.toml":          "Rust",
    "Cargo.lock":          "Rust",
    "pom.xml":             "Java",
    "build.gradle":        "Kotlin",
    "build.gradle.kts":    "Kotlin",
    "settings.gradle":     "Java",
    "build.sbt":           "Scala",
    "CMakeLists.txt":      "C++",
    "Gemfile":             "Ruby",
    "Gemfile.lock":        "Ruby",
    "composer.json":       "PHP",
    "composer.lock":       "PHP",
    "environment.yml":     "Python",
    "environment.yaml":    "Python",
    "conda.yml":           "Python",
    "conda.yaml":          "Python",
    "Package.swift":       "Swift",
    "mix.exs":             "Elixir",
    "stack.yaml":          "Haskell",
    "default.nix":         "Nix",
    "flake.nix":           "Nix",
    "rockspec":            "Lua",
}

# ------------------------------------------------------------------ #
# Documentation Files                                                  #
# ------------------------------------------------------------------ #

DOCUMENTATION_FILE_NAMES: set[str] = {
    "README.md", "README.rst", "README.txt", "README",
    "CHANGELOG.md", "CHANGELOG.rst", "CHANGELOG.txt",
    "CONTRIBUTING.md", "CONTRIBUTING.rst",
    "ARCHITECTURE.md", "DESIGN.md",
    "LICENSE", "LICENSE.md", "LICENSE.txt",
    "AUTHORS", "AUTHORS.md",
    "HISTORY.md", "NOTICE.md",
    "TODO.md", "ROADMAP.md",
}

# ------------------------------------------------------------------ #
# Test Directories                                                     #
# ------------------------------------------------------------------ #

TEST_DIR_NAMES: set[str] = {
    "tests", "test", "testing",
    "spec", "specs",
    "unit_tests", "integration_tests", "e2e_tests",
}

# ------------------------------------------------------------------ #
# Dependency Files                                                     #
# ------------------------------------------------------------------ #

DEPENDENCY_FILES: list[str] = [
    "requirements.txt",
    "package.json",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "requirements-dev.txt",
    "requirements_dev.txt",
    "requirements-prod.txt",
    "requirements-staging.txt",
    "requirements-test.txt",
    "requirements-base.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "environment.yml",
    "environment.yaml",
    "conda.yml",
    "conda.yaml",
]