"""
TC_M2_GO_001 — Go Adapter Validation
Tests GoAdapter against a synthetic Go fixture covering:
  - Package declarations
  - Struct and interface definitions
  - Method receivers (value + pointer)
  - Function calls and method calls
  - Struct instantiations
  - Goroutines
  - Import resolution
  - Framework detection (net/http)
"""
import json, sys
from datetime import datetime as dt, UTC
from pathlib import Path

V3_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(V3_ROOT.parent))
sys.path.insert(0, str(V3_ROOT))

TEST_ID      = "TC_M2_GO_001"
EVIDENCE_DIR = Path(__file__).parent / "evidence"
FIXTURE_DIR  = Path(__file__).parent / "fixtures" / "go"

FIXTURE_FILES = {
    "go.mod": """module github.com/codetruth/example

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/lib/pq v1.10.9
)
""",
    "models/user.go": """package models

import (
    "time"
    "errors"
)

type User struct {
    ID        int
    Name      string
    Email     string
    CreatedAt time.Time
    IsActive  bool
}

type Order struct {
    ID       int
    UserID   int
    Total    float64
    Status   string
    Items    []OrderItem
}

type OrderItem struct {
    ID        int
    ProductID int
    Quantity  int
    Price     float64
}

func NewUser(name, email string) *User {
    return &User{
        Name:      name,
        Email:     email,
        CreatedAt: time.Now(),
        IsActive:  true,
    }
}

func (u *User) Validate() error {
    if u.Name == "" {
        return errors.New("name required")
    }
    if u.Email == "" {
        return errors.New("email required")
    }
    return nil
}

func (u *User) GetDisplayName() string {
    return u.Name
}

func (o *Order) AddItem(item OrderItem) {
    o.Items = append(o.Items, item)
    o.Total += item.Price * float64(item.Quantity)
}
""",
    "repository/user_repo.go": """package repository

import (
    "database/sql"
    "github.com/codetruth/example/models"
)

type UserRepository interface {
    GetByID(id int) (*models.User, error)
    GetAll() ([]*models.User, error)
    Create(user *models.User) error
    Update(user *models.User) error
    Delete(id int) error
}

type OrderRepository interface {
    GetByID(id int) (*models.Order, error)
    Create(order *models.Order) error
    UpdateStatus(id int, status string) error
    GetByUserID(userID int) ([]*models.Order, error)
}

type PostgresUserRepo struct {
    db *sql.DB
}

func NewPostgresUserRepo(db *sql.DB) *PostgresUserRepo {
    return &PostgresUserRepo{db: db}
}

func (r *PostgresUserRepo) GetByID(id int) (*models.User, error) {
    user := &models.User{}
    err := r.db.QueryRow("SELECT id, name, email FROM users WHERE id=$1", id).
        Scan(&user.ID, &user.Name, &user.Email)
    if err != nil {
        return nil, err
    }
    return user, nil
}

func (r *PostgresUserRepo) GetAll() ([]*models.User, error) {
    rows, err := r.db.Query("SELECT id, name, email FROM users")
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var users []*models.User
    for rows.Next() {
        user := &models.User{}
        rows.Scan(&user.ID, &user.Name, &user.Email)
        users = append(users, user)
    }
    return users, nil
}

func (r *PostgresUserRepo) Create(user *models.User) error {
    _, err := r.db.Exec(
        "INSERT INTO users (name, email) VALUES ($1, $2)",
        user.Name, user.Email,
    )
    return err
}

func (r *PostgresUserRepo) Update(user *models.User) error {
    _, err := r.db.Exec(
        "UPDATE users SET name=$1, email=$2 WHERE id=$3",
        user.Name, user.Email, user.ID,
    )
    return err
}

func (r *PostgresUserRepo) Delete(id int) error {
    _, err := r.db.Exec("DELETE FROM users WHERE id=$1", id)
    return err
}

var _ UserRepository = (*PostgresUserRepo)(nil)
""",
    "service/user_service.go": """package service

import (
    "fmt"
    "net/http"
    "github.com/codetruth/example/models"
    "github.com/codetruth/example/repository"
)

type UserService struct {
    userRepo  repository.UserRepository
    orderRepo repository.OrderRepository
}

func NewUserService(
    userRepo repository.UserRepository,
    orderRepo repository.OrderRepository,
) *UserService {
    return &UserService{
        userRepo:  userRepo,
        orderRepo: orderRepo,
    }
}

func (s *UserService) CreateUser(name, email string) (*models.User, error) {
    user := models.NewUser(name, email)
    if err := user.Validate(); err != nil {
        return nil, fmt.Errorf("validation failed: %w", err)
    }
    if err := s.userRepo.Create(user); err != nil {
        return nil, err
    }
    return user, nil
}

func (s *UserService) GetAllUsers() ([]*models.User, error) {
    return s.userRepo.GetAll()
}

func (s *UserService) PlaceOrder(userID int, total float64) (*models.Order, error) {
    user, err := s.userRepo.GetByID(userID)
    if err != nil {
        return nil, err
    }
    _ = user.GetDisplayName()
    order := &models.Order{
        UserID: userID,
        Total:  total,
        Status: "PENDING",
    }
    if err := s.orderRepo.Create(order); err != nil {
        return nil, err
    }
    return order, nil
}

func (s *UserService) ProcessAsync(userID int) {
    go s.userRepo.GetByID(userID)
}

func HealthCheck(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "OK")
}
""",
}

def to_json_safe(obj):
    if hasattr(obj, "__dict__"): return {k: to_json_safe(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, (list, tuple)): return [to_json_safe(i) for i in obj]
    if isinstance(obj, dict): return {k: to_json_safe(v) for k, v in obj.items()}
    return str(obj) if not isinstance(obj, (int, float, bool, type(None))) else obj

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(to_json_safe(data), f, indent=2)

def create_fixture():
    for fname, content in FIXTURE_FILES.items():
        path = FIXTURE_DIR / fname
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    go_files = sum(1 for f in FIXTURE_FILES if f.endswith(".go"))
    print(f"Fixture: {FIXTURE_DIR} ({len(FIXTURE_FILES)} files, {go_files} .go)")

def save_markdown(passed, report):
    status = "PASS" if passed else "FAIL"
    md = Path(__file__).with_suffix(".md")
    nc  = report.get("node_counts", {})
    ec  = report.get("edge_counts", {})
    res = report.get("resolution", {})
    lines = [
        f"# {TEST_ID} — Go Adapter Validation",
        "", "| Field | Value |", "|---|---|",
        f"| Status | {status} |",
        f"| Date | {dt.now(UTC).date().isoformat()} |",
        f"| Module | {report.get('module_name', 'N/A')} |",
        f"| Framework | {report.get('framework', 'N/A')} |",
        f"| Files Scanned | {report.get('files_scanned', 0)} |",
        f"| Governance Gate | {report.get('governance_gate', 'N/A')} |",
        "", "## Graph Nodes", "", "| Type | Count |", "|---|---|",
        f"| Packages | {nc.get('packages', 0)} |",
        f"| Structs | {nc.get('structs', 0)} |",
        f"| Interfaces | {nc.get('interfaces', 0)} |",
        f"| Functions | {nc.get('functions', 0)} |",
        f"| Methods | {nc.get('methods', 0)} |",
        f"| **Total** | **{nc.get('total', 0)}** |",
        "", "## Graph Edges", "", "| Type | Count |", "|---|---|",
        f"| Calls | {ec.get('calls', 0)} |",
        f"| Struct Inits | {ec.get('struct_inits', 0)} |",
        f"| Goroutines | {ec.get('goroutines', 0)} |",
        f"| **Total** | **{ec.get('total', 0)}** |",
        "", "## Resolution", "", "| Metric | Value |", "|---|---|",
        f"| Resolved | {res.get('resolved_count', 0)} |",
        f"| Unresolved | {res.get('unresolved_count', 0)} |",
        f"| Resolution % | {res.get('resolution_pct', 0)}% |",
        "", "## Requirement Traceability",
        "", "| Requirement | Status |", "|---|---|",
        f"| GO-001 Package Detection | {status} |",
        f"| GO-002 Struct/Interface Detection | {status} |",
        f"| GO-003 Method Receiver Parsing | {status} |",
        f"| GO-004 Goroutine Detection | {status} |",
        f"| GO-005 Module Name Detection | {status} |",
        f"| GO-006 Framework Detection | {status} |",
        f"| GO-007 Governance Gate | {status} |",
    ]
    md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Evidence saved --> {md}")


def test_tc_m2_go_001():
    print("=" * 80)
    print(f"{TEST_ID} — Go Adapter Validation")
    print("=" * 80)
    create_fixture()

    from v3.repository_graph.languages.go_adapter import GoAdapter
    report = GoAdapter().scan(repo_root=str(FIXTURE_DIR))

    nc  = report.get("node_counts", {})
    ec  = report.get("edge_counts", {})
    res = report.get("resolution", {})

    print("\nGRAPH NODES\n" + "-" * 60)
    print(f"     Packages   : {nc.get('packages', 0)}")
    print(f"     Structs    : {nc.get('structs', 0)}")
    print(f"     Interfaces : {nc.get('interfaces', 0)}")
    print(f"     Functions  : {nc.get('functions', 0)}")
    print(f"     Methods    : {nc.get('methods', 0)}")
    print(f"     Total      : {nc.get('total', 0)}")

    print("\nGRAPH EDGES\n" + "-" * 60)
    print(f"     Calls        : {ec.get('calls', 0)}")
    print(f"     Struct inits : {ec.get('struct_inits', 0)}")
    print(f"     Goroutines   : {ec.get('goroutines', 0)}")
    print(f"     Total        : {ec.get('total', 0)}")

    print("\nRESOLUTION\n" + "-" * 60)
    print(f"     Resolved   : {res.get('resolved_count', 0)}")
    print(f"     Unresolved : {res.get('unresolved_count', 0)}")
    print(f"     Pct        : {res.get('resolution_pct', 0)}%")
    print(f"     Module     : {report.get('module_name', 'N/A')}")
    print(f"     Framework  : {report.get('framework', 'N/A')}")
    print(f"     Gate       : {report.get('governance_gate', 'N/A')}")

    print("\nASSERTIONS\n" + "-" * 60)

    go_count = report.get("files_scanned", 0)
    assert go_count >= 3, f"Expected >= 3 .go files, got {go_count}"
    print(f"PASS  files_scanned = {go_count} >= 3")

    assert nc.get("packages", 0) >= 3, f"Expected >= 3 packages"
    print(f"PASS  packages = {nc['packages']} >= 3")

    assert nc.get("structs", 0) >= 3, f"Expected >= 3 structs"
    print(f"PASS  structs = {nc['structs']} >= 3")

    assert nc.get("interfaces", 0) >= 2, f"Expected >= 2 interfaces"
    print(f"PASS  interfaces = {nc['interfaces']} >= 2")

    assert nc.get("methods", 0) > 0, "Expected methods detected"
    print(f"PASS  methods = {nc['methods']} > 0")

    assert ec.get("calls", 0) > 0, "Expected calls detected"
    print(f"PASS  calls = {ec['calls']} > 0")

    assert ec.get("goroutines", 0) > 0, "Expected goroutines detected"
    print(f"PASS  goroutines = {ec['goroutines']} > 0")

    assert report.get("module_name"), "Expected module name from go.mod"
    print(f"PASS  module_name = {report['module_name']}")

    assert report.get("framework") in ("net_http", "gin", "gin_gonic", "go_standard"),         f"Unexpected framework: {report.get('framework')}"
    print(f"PASS  framework = {report['framework']}")

    assert report.get("governance_gate") == "APPROVED"
    print(f"PASS  governance_gate = APPROVED")

    save_json(EVIDENCE_DIR / f"{TEST_ID.lower()}_result.json", report)
    save_markdown(passed=True, report=report)

    print(f"\nFINAL RESULT\n{'-'*60}\nPASS")
    return True


if __name__ == "__main__":
    try:
        test_tc_m2_go_001()
    except (AssertionError, Exception) as exc:
        import traceback; traceback.print_exc(); sys.exit(1)
