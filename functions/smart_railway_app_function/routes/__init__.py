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

    # Passengers routes
    from routes.passengers import passengers_bp
    app.register_blueprint(passengers_bp)

    # Coach Layouts routes
    from routes.coach_layouts import coach_layouts_bp
    app.register_blueprint(coach_layouts_bp)

    # Data Seeding routes (create test users)
    from routes.seed import seed_bp
    app.register_blueprint(seed_bp)

    # Comprehensive Sample Data Seeder
    from routes.data_seed import data_seed_bp
    app.register_blueprint(data_seed_bp)

    # Public Sample Data Seeder (No Auth Required)
    from routes.public_seed import public_seed_bp
    app.register_blueprint(public_seed_bp)

    # CloudScale Direct Test (Debug)
    from routes.cloudscale_test import cloudscale_test_bp
    app.register_blueprint(cloudscale_test_bp)

    # Smart Sample Data Seeder (Schema-Aware)
    from routes.smart_seed import smart_seed_bp
    app.register_blueprint(smart_seed_bp)

    # Direct CloudScale Data Creator (Guaranteed Working)
    from routes.direct_data import direct_data_bp
    app.register_blueprint(direct_data_bp)

    # Railway Modules Data Creator (Targeted)
    from routes.railway_data import railway_data_bp
    app.register_blueprint(railway_data_bp)

    # CloudScale Schema Discovery
    from routes.schema_discovery import schema_discovery_bp
    app.register_blueprint(schema_discovery_bp)

    # Expand Railway Data (Build on Successful Patterns)
    from routes.expand_railway import expand_railway_bp
    app.register_blueprint(expand_railway_bp)

    # Reliable Railway Data Creation (CloudScale Persistence Fix)
    from routes.reliable_railway_data import reliable_railway_data_bp
    app.register_blueprint(reliable_railway_data_bp)
