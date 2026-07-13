
using System;
using System.Collections.Generic;

namespace ECommerceApp.Models
{
    public class User
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public string Email { get; set; }
        public DateTime CreatedAt { get; set; }
        public bool IsActive { get; set; }

        public User(string name, string email)
        {
            Name = name;
            Email = email;
            CreatedAt = DateTime.Now;
            IsActive = true;
        }

        public string GetDisplayName()
        {
            return Name.ToUpper();
        }

        public bool Validate()
        {
            return !string.IsNullOrEmpty(Name) &&
                   Email.Contains("@");
        }
    }

    public class Order
    {
        public int Id { get; set; }
        public int UserId { get; set; }
        public decimal Total { get; set; }
        public string Status { get; set; }
        public List<OrderItem> Items { get; set; }

        public Order(int userId, decimal total)
        {
            UserId = userId;
            Total = total;
            Status = "PENDING";
            Items = new List<OrderItem>();
        }

        public void AddItem(OrderItem item)
        {
            Items.Add(item);
            Total += item.Price * item.Quantity;
        }
    }

    public class OrderItem
    {
        public int Id { get; set; }
        public int ProductId { get; set; }
        public int Quantity { get; set; }
        public decimal Price { get; set; }
    }
}
