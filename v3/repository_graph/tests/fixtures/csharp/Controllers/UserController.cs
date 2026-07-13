
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using ECommerceApp.Services;
using ECommerceApp.Models;

namespace ECommerceApp.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class UserController : ControllerBase
    {
        private readonly UserService _userService;
        private readonly OrderService _orderService;

        public UserController(UserService userService, OrderService orderService)
        {
            _userService  = userService;
            _orderService = orderService;
        }

        [HttpPost]
        public async Task<IActionResult> CreateUser(string name, string email)
        {
            var user = await _userService.CreateUserAsync(name, email);
            return Ok(user);
        }

        [HttpGet]
        public async Task<IActionResult> GetUsers()
        {
            var users = await _userService.GetActiveUsersAsync();
            return Ok(users);
        }

        [HttpPost("{userId}/orders")]
        public async Task<IActionResult> PlaceOrder(int userId, decimal total)
        {
            var order = await _userService.PlaceOrderAsync(userId, total);
            return Ok(order);
        }

        [HttpDelete("{orderId}")]
        public async Task<IActionResult> CancelOrder(int orderId)
        {
            var result = await _orderService.CancelOrderAsync(orderId);
            return result ? Ok() : BadRequest();
        }
    }
}
