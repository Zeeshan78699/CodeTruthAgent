"""
TC_V2_045 integration fixture.
Contains real Python functions exercising different behavior categories.
"""

import os
import shutil


# -----------------------------------------------------
# Backup / Recovery pair (OPPOSING)
# -----------------------------------------------------

def create_backup(source_path, backup_path):
    """Copy a file to backup location."""
    shutil.copy2(source_path, backup_path)
    return True


def restore_backup(backup_path, target_path):
    """Restore a file from backup."""
    shutil.copy2(backup_path, target_path)
    os.remove(backup_path)
    return True


# -----------------------------------------------------
# Save / Store pair (SIMILAR)
# -----------------------------------------------------

def save_user_data(user_id, data):
    """Write user data to disk."""
    with open(f"users/{user_id}.json", "w") as f:
        f.write(data)
    return True


def store_user_data(user_id, data):
    """Persist user data to disk."""
    with open(f"users/{user_id}.json", "w") as f:
        f.write(data)
    return True


# -----------------------------------------------------
# Delete / Cleanup pair (SHARED HIGH IMPACT)
# -----------------------------------------------------

def delete_temp_file(path):
    """Remove a temporary file."""
    os.remove(path)
    return True


def cleanup_temp_file(path):
    """Clean up temporary file."""
    os.remove(path)
    return True


# -----------------------------------------------------
# Pure functions (BOTH CLEAN)
# -----------------------------------------------------

def calculate_sum(values):
    """Sum a list of numbers."""
    total = 0
    for value in values:
        total = total + value
    return total


def add_numbers(numbers):
    """Add up a list of numbers."""
    result = 0
    for number in numbers:
        result = result + number
    return result


# -----------------------------------------------------
# Unrelated functions (BLOCK case)
# -----------------------------------------------------

def send_email_notification(recipient, subject, body):
    """Send a notification email."""
    import requests
    requests.request(
        "POST",
        "https://api.email.example.com/send",
        json={"to": recipient, "subject": subject, "body": body},
    )
    return True


def calculate_invoice_total(items, tax_rate):
    """Compute invoice total with tax."""
    subtotal = 0
    for item in items:
        subtotal = subtotal + item["price"]
    total = subtotal * (1 + tax_rate)
    return total


# -----------------------------------------------------
# Auth domain pair (SAME DOMAIN, DIFFERENT NAMES)
# -----------------------------------------------------

def authenticate_user(username, password):
    """Verify user credentials and return auth token."""
    token = authenticate(username, password)
    return token


def validate_login(username, password):
    """Validate login credentials."""
    token = authenticate(username, password)
    return token


def authenticate(user, pwd):
    """Internal auth helper."""
    return "fake_token_xyz"
