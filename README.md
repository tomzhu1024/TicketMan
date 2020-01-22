# TicketMan

Air ticket reservation system.

NYU Shanghai Databases final project.

## Project Structure

- **static** *– static resources folder*
  - **image** *– images folder*
  - **js** *– JavaScript files folder*
    - calDo.js *– initialize date picker widget*
    - formVldt.js *– general form validator functions*
    - loginE.js *– login form validator functions*
    - loginU.js *– login form validator functions*
  - **libs** *– 3rd party libraries folder*
- **templates** *– web page templates*
  - 403.html *– 404 error page*
  - 404.html *– 403 error page*
  - 500.html *– 500 error page*
  - addAirplane.html *– adding airplane page for airline staff*
  - addAirport.html *– adding airport page for airline staff*
  - addFlight.html *– adding flight result page for airline staff*
  - adminPanel.html *– admin panel page for admin*
  - adminPanelMsg.html *– admin panel result page for admin*
  - compareRevenue.html *– compare revenue page for airline staff*
  - loginAdmin.html *– login as admin page*
  - loginAirlineStaff.html *– login as airline staff page*
  - loginBookingAgent.html *– login as booking agent page*
  - loginCustomer.html *– login as customer page*
  - logout.html *– log out message page*
  - manageMyFlight.html *– view/add flights page for airline staff*
  - registerAirlineStaff.html *– register as airline staff page*
  - registerBookingAgent.html *– register as booking agent page*
  - registerCustomer.html *– register as customer page*
  - searchFlightByFlightNum.html *– search flight by flight number page*
  - searchFlightByLocation.html *– search flight by locations page*
  - setup1.html *– application setup page*
  - setup2.html *– application setup page*
  - setup3.html *– application setup page*
  - TemplateError.html *– base template for error pages*
  - TemplateNavBar.html *– base template with full nav-bar*
  - TemplateNavBarLite.html *– base template with clean nav-bar*
  - TemplateSetup.html *– base template for setup pages*
  - totalTicketSold.html *– total ticket sold page for airline staff*
  - trackMySpending.html *– track my spending page for customer*
  - updateStatus.html *– update flight status result page for airline staff*
  - viewCustomerFlightHistory.html *– view historical flight page for customer*
  - viewFrequentCustomer.html *– view frequent customer page for booking agent*
  - viewMyCommission.html – view my commission page for booking agent
  - viewMyFlight.html *– view my flight page for customer and booking agent*
  - viewPassengers.html *– view passengers page for airline staff*
  - viewTopBookingAgents.html *– view top booking agent page for airline staff*
  - viewTopCustomers.html *– view top customers page for booking agent*
  - viewTopDestinations.html *– view top destinations page for airline staff*
- app.py *– Flask part and main backend business logic*
- cdnjs_downloader.py - *download libraries from cdnjs.com*
- colored_logger.py *– make the log more colorful*
- create_tables.sql *– SQL commands to initialize the schemes*
- import_test_data.sql *– SQL commands to insert test data*
- mysql_utils.py *– SQL part and database business logic*