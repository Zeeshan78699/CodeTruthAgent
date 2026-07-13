
using System.Collections.Generic;
using System.Threading.Tasks;
using ECommerceApp.Models;

namespace ECommerceApp.Interfaces
{
    public interface IUserRepository
    {
        Task<User> GetByIdAsync(int id);
        Task<IEnumerable<User>> GetAllAsync();
        Task<User> CreateAsync(User user);
        Task UpdateAsync(User user);
        Task DeleteAsync(int id);
    }

    public interface IOrderRepository
    {
        Task<Order> GetByIdAsync(int id);
        Task<Order> CreateAsync(Order order);
        Task UpdateStatusAsync(int id, string status);
        Task<IEnumerable<Order>> GetByUserIdAsync(int userId);
    }

    public interface IEmailService
    {
        Task SendWelcomeEmailAsync(User user);
        Task SendOrderConfirmationAsync(Order order, User user);
        bool ValidateEmail(string email);
    }
}
