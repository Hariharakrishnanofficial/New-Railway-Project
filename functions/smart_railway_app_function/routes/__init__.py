"""
Routes module - Blueprint registration for Flask app.
"""

def register_blueprints(app):
    """Register all API route blueprints with the Flask app."""

    # Auth routes (register, login, logout, refresh, etc.)
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    # User management routes
    from routes.users import users_bp
    app.register_blueprint(users_bp)

    # Train routes
    from routes.trains import trains_bp
    app.register_blueprint(trains_bp)

    # Station routes
    from routes.stations import stations_bp
    app.register_blueprint(stations_bp)

    # Train routes (with stops)
    from routes.train_routes import train_routes_bp
    app.register_blueprint(train_routes_bp)

    # Booking routes
    from routes.bookings import bookings_bp
    app.register_blueprint(bookings_bp)

    # Fare routes
    from routes.fares import fares_bp
    app.register_blueprint(fares_bp)

    # Inventory routes
    from routes.inventory import inventory_bp
    app.register_blueprint(inventory_bp)

    # Quota routes
    from routes.quotas import quotas_bp
    app.register_blueprint(quotas_bp)

    # Announcement routes
    from routes.announcements import announcements_bp
    app.register_blueprint(announcements_bp)

    # Settings routes
    from routes.settings import settings_bp
    app.register_blueprint(settings_bp)

    # Admin logs routes
    from routes.admin_logs import admin_logs_bp
    app.register_blueprint(admin_logs_bp)

    # Admin users routes
    from routes.admin_users import admin_users_bp
    app.register_blueprint(admin_users_bp)

    # Module Master routes
    from routes.module_master import module_master_bp
    app.register_blueprint(module_master_bp)
