package repository

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
