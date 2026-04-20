"""
Train Controller

Business logic for train operations.
"""

from typing import Dict, List, Optional, Tuple
from controllers.base_controller import BaseController
from models.train import Train
from config import TABLES


class TrainController(BaseController):
    """Controller for train-related operations."""

    def __init__(self):
        super().__init__(TABLES.get('trains', 'Trains'), Train)

    def search_trains(self, source_station_id: str, destination_station_id: str,
                     date: str = None) -> List[Dict]:
        """
        Search trains between two stations.

        Args:
            source_station_id: Source station ROWID
            destination_station_id: Destination station ROWID
            date: Optional journey date

        Returns:
            List of matching trains
        """
        filters = {
            'Source_Station_ID': source_station_id,
            'Destination_Station_ID': destination_station_id,
            'Is_Active': True
        }

        trains = self.repo.find_many(filters)

        # Filter by running days if date provided
        if date and trains:
            from datetime import datetime
            try:
                day_name = datetime.strptime(date, '%Y-%m-%d').strftime('%a')
                trains = [t for t in trains if day_name in t.get('Running_Days', '')]
            except ValueError:
                pass

        return trains

    def get_train_by_number(self, train_number: str) -> Optional[Dict]:
        """Get train by train number."""
        return self.repo.find_one({'Train_Number': train_number})

    def get_train_schedule(self, train_id: str) -> List[Dict]:
        """Get train schedule (all stops)."""
        from repositories.cloudscale_repository import CloudScaleRepository
        route_repo = CloudScaleRepository(TABLES.get('routes', 'Routes'))
        routes = route_repo.find_many({'Train_ID': train_id})
        return sorted(routes, key=lambda x: x.get('Sequence_Number', 0))

    def get_seat_availability(self, train_id: str, date: str,
                             class_type: str) -> Dict:
        """
        Get seat availability for a train on specific date.

        Returns:
            Dictionary with available, waitlist, and RAC counts
        """
        train = self.get_by_id(train_id)
        if not train:
            return {'available': 0, 'waitlist': 0, 'rac': 0}

        # Get total seats for class
        class_field_map = {
            '1A': 'AC_First_Class',
            '2A': 'AC_2_Tier',
            '3A': 'AC_3_Tier',
            'SL': 'Sleeper',
            'GN': 'General',
        }
        total_seats = train.get(class_field_map.get(class_type, 'Total_Seats'), 0)

        # Count existing bookings
        from repositories.cloudscale_repository import CloudScaleRepository
        booking_repo = CloudScaleRepository(TABLES.get('bookings', 'Bookings'))
        bookings = booking_repo.find_many({
            'Train_ID': train_id,
            'Journey_Date': date,
            'Class': class_type,
            'Status': ['Confirmed', 'RAC']  # Exclude cancelled
        })

        booked = sum(b.get('Passengers', 1) for b in bookings
                    if b.get('Status') == 'Confirmed')
        rac_count = sum(b.get('Passengers', 1) for b in bookings
                       if b.get('Status') == 'RAC')

        available = max(0, total_seats - booked)
        max_rac = int(total_seats * 0.1)  # 10% RAC quota

        return {
            'total_seats': total_seats,
            'available': available,
            'booked': booked,
            'rac': rac_count,
            'rac_available': max(0, max_rac - rac_count),
            'waitlist': 0 if available > 0 else 1,
        }

    def update_train_status(self, train_id: str, is_active: bool) -> Tuple[bool, Optional[str]]:
        """Activate or deactivate a train."""
        result, error = self.update(train_id, {'Is_Active': is_active})
        return result is not None, error
