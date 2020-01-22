INSERT INTO `airline` (`airline_name`) VALUES
('Air New Zealand'),
('Qantas'),
('Qatar Airways'),
('Singapore Airline');
INSERT INTO `airline_staff` (`username`, `password`, `first_name`, `last_name`, `date_of_birth`, `airline_name`) VALUES
('qantas', '6fb57515e9826f894eab27d737d6f4c98365a1ab', 'Robert', 'Zhang', '2000-08-24', 'Qantas'),
('qatar', '133f5f567509940df6c46c9597e28f976a75fa71', 'Zavier', 'He', '1999-11-30', 'Qatar Airways');
INSERT INTO `airplane` (`airline_name`, `airplane_id`, `seats`) VALUES
('Qatar Airways', 1024, 420),
('Qatar Airways', 1025, 300),
('Qatar Airways', 1026, 350),
('Qatar Airways', 2008, 10);
INSERT INTO `airport` (`airport_name`, `airport_city`) VALUES
('Capital International Airport', 'Beijing'),
('Dubai International Airport', 'Dubai'),
('Haneda Airport', 'Tokyo'),
('Heathrow Airport', 'London'),
('Los Angeles International Airport', 'Los Angeles'),
("O'Hare International Airport", 'Chicago');
INSERT INTO `booking_agent` (`email`, `password`, `booking_agent_id`) VALUES
('alexshen@nyu.edu', '698a0c125e5d9d5a168b16342566e5bb55bc1420', 5012),
('tomzhu@nyu.edu', '4a27a0aa165aaaba91c1f2e201119e05d546f0d1', 3599);
INSERT INTO `customer` (`email`, `name`, `password`, `building_number`, `street`, `city`, `state`, `phone_number`, `passport_number`, `passport_expiration`, `passport_country`, `date_of_birth`) VALUES
('ca@nyu.edu', 'Customer A', '1c42c72cf95aa1b76609b585b34baf6b501d713e', '1555', 'Century Avn', 'Shanghai', 'Shanghai', 134567890, 'XA1257772', '2020-04-22', 'China', '2000-11-07'),
('cb@nyu.edu', 'Customer B', '1c42c72cf95aa1b76609b585b34baf6b501d713e', '1555', 'Century Avn', 'Shanghai', 'Shanghai', 134567890, 'XA1257772', '2020-04-22', 'China', '2000-11-07'),
('cc@nyu.edu', 'Customer C', '1c42c72cf95aa1b76609b585b34baf6b501d713e', '1555', 'Century Avn', 'Shanghai', 'Shanghai', 134567890, 'XA1257772', '2020-04-22', 'China', '2000-11-07'),
('cd@nyu.edu', 'Customer D', '1c42c72cf95aa1b76609b585b34baf6b501d713e', '1555', 'Century Avn', 'Shanghai', 'Shanghai', 134567890, 'XA1257772', '2020-04-22', 'China', '2000-11-07');
INSERT INTO `flight` (`airline_name`, `flight_num`, `departure_airport`, `departure_time`, `arrival_airport`, `arrival_time`, `price`, `status`, `airplane_id`) VALUES
('Qatar Airways', 370, 'Capital International Airport', '2019-12-13 10:20:00', 'Dubai International Airport', '2019-12-13 22:35:00', '5500', 'Upcoming', 1025),
('Qatar Airways', 466, 'Haneda Airport', '2019-12-09 05:00:00', 'Heathrow Airport', '2019-12-09 18:35:00', '3299', 'Upcoming', 1025),
('Qatar Airways', 1022, 'Los Angeles International Airport', '2019-12-05 06:00:00', 'Capital International Airport', '2019-12-06 14:35:00', '8200', 'Upcoming', 1025);
INSERT INTO `ticket` (`ticket_id`, `airline_name`, `flight_num`) VALUES
(1, 'Qatar Airways', 370),
(3, 'Qatar Airways', 466),
(4, 'Qatar Airways', 466),
(5, 'Qatar Airways', 466),
(2, 'Qatar Airways', 1022),
(6, 'Qatar Airways', 1022);
INSERT INTO `purchases` (`ticket_id`, `customer_email`, `booking_agent_id`, `purchase_date`) VALUES
(1, 'ca@nyu.edu', NULL, '2019-11-15'),
(2, 'ca@nyu.edu', NULL, '2019-12-12'),
(3, 'ca@nyu.edu', NULL, '2019-10-12'),
(4, 'cc@nyu.edu', 5012, '2019-12-12'),
(5, 'cd@nyu.edu', 5012, '2019-12-12'),
(6, 'ca@nyu.edu', 5012, '2019-12-12');
