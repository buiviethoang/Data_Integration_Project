from api.db import mongodb


class CarFilter():
    def __init__(self):
        self.car_db = mongodb['car']