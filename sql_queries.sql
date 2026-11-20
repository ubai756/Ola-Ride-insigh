-- =====================================================================
-- OLA RIDE INSIGHTS - SQL QUERIES  (SQLite / works in MySQL too)
-- Table: rides   (created by data_cleaning.py)
-- =====================================================================


-- 1. Retrieve all successful bookings
SELECT *
FROM rides
WHERE Booking_Status = 'Success';


-- 2. Average ride distance for each vehicle type
--    (all bookings, same basis as the reference sheet in the dataset)
SELECT Vehicle_Type,
       ROUND(AVG(Ride_Distance), 2) AS Avg_Ride_Distance_Km
FROM rides
GROUP BY Vehicle_Type
ORDER BY Avg_Ride_Distance_Km DESC;

-- 2b. Same, but only for successful rides (cancelled rides have 0 km,
--     which pulls the average down - this is the more realistic number)
SELECT Vehicle_Type,
       ROUND(AVG(Ride_Distance), 2) AS Avg_Distance_Completed_Rides_Km
FROM rides
WHERE Booking_Status = 'Success'
GROUP BY Vehicle_Type
ORDER BY Avg_Distance_Completed_Rides_Km DESC;


-- 3. Total number of rides cancelled by customers
SELECT COUNT(*) AS Total_Cancelled_By_Customers
FROM rides
WHERE Booking_Status = 'Canceled by Customer';


-- 4. Top 5 customers with the highest number of rides
SELECT Customer_ID,
       COUNT(*) AS Total_Rides
FROM rides
GROUP BY Customer_ID
ORDER BY Total_Rides DESC, Customer_ID
LIMIT 5;


-- 5. Rides cancelled by drivers due to personal and car related issues
SELECT COUNT(*) AS Driver_Cancels_Personal_Car_Issue
FROM rides
WHERE Canceled_Rides_by_Driver = 'Personal & Car related issue';


-- 6. Maximum and minimum driver ratings for Prime Sedan bookings
SELECT MAX(Driver_Ratings) AS Max_Driver_Rating,
       MIN(Driver_Ratings) AS Min_Driver_Rating
FROM rides
WHERE Vehicle_Type = 'Prime Sedan'
  AND Driver_Ratings IS NOT NULL;


-- 7. All rides where payment was made using UPI
SELECT *
FROM rides
WHERE Payment_Method = 'UPI';


-- 8. Average customer rating per vehicle type
SELECT Vehicle_Type,
       ROUND(AVG(Customer_Rating), 2) AS Avg_Customer_Rating
FROM rides
WHERE Customer_Rating IS NOT NULL
GROUP BY Vehicle_Type
ORDER BY Avg_Customer_Rating DESC;


-- 9. Total booking value of rides completed successfully
SELECT SUM(Booking_Value) AS Total_Booking_Value_Successful_Rides
FROM rides
WHERE Booking_Status = 'Success';


-- 10. All incomplete rides along with the reason
SELECT Booking_ID,
       Customer_ID,
       Vehicle_Type,
       Incomplete_Rides_Reason
FROM rides
WHERE Incomplete_Rides = 'Yes';
