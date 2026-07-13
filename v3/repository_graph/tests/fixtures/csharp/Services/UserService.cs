
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using ECommerceApp.Interfaces;
using ECommerceApp.Models;

namespace ECommerceApp.Services
{
    public class UserService
    {
        private readonly IUserRepository _userRepository;
        private readonly IEmailService _emailService;
        private readonly IOrderRepository _orderRepository;

        public UserService(
            IUserRepository userRepository,
            IEmailService emailService,
            IOrderRepository orderRepository)
        {
            _userRepository  = userRepository;
            _emailService    = emailService;
            _orderRepository = orderRepository;
        }

        public async Task<User> CreateUserAsync(string name, string email)
        {
            var user = new User(name, email);
            if (!user.Validate())
                throw new ArgumentException("Invalid user data");

            var created = await _userRepository.CreateAsync(user);
            await _emailService.SendWelcomeEmailAsync(created);
            return created;
        }

        public async Task<IEnumerable<User>> GetActiveUsersAsync()
        {
            var users = await _userRepository.GetAllAsync();
            return users;
        }

        public async Task<Order> PlaceOrderAsync(int userId, decimal total)
        {
            var user  = await _userRepository.GetByIdAsync(userId);
            var order = new Order(userId, total);
            var created = await _orderRepository.CreateAsync(order);
            await _emailService.SendOrderConfirmationAsync(created, user);
            return created;
        }
    }

    public class OrderService
    {
        private readonly IOrderRepository _orderRepository;
        private readonly IUserRepository _userRepository;

        public OrderService(
            IOrderRepository orderRepository,
            IUserRepository userRepository)
        {
            _orderRepository = orderRepository;
            _userRepository  = userRepository;
        }

        public async Task<bool> CancelOrderAsync(int orderId)
        {
            var order = await _orderRepository.GetByIdAsync(orderId);
            if (order.Status == "COMPLETED")
                return false;

            await _orderRepository.UpdateStatusAsync(orderId, "CANCELLED");
            return true;
        }

        public async Task<IEnumerable<Order>> GetUserOrdersAsync(int userId)
        {
            var user   = await _userRepository.GetByIdAsync(userId);
            var orders = await _orderRepository.GetByUserIdAsync(userId);
            return orders;
        }
    }
}
