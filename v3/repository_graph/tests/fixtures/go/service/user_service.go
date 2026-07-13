package service

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
