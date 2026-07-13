package models

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
