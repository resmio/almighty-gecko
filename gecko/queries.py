QUERIES = {
    'bookings_and_facilities':

    """
        SELECT b.created, f.id AS facility_id, f.created AS f_created
        FROM bookoya_booking b
        FULL OUTER JOIN bookoya_facility f ON f.id = b.facility_id
        WHERE f.verified IS TRUE

    """,

    'bookings':

    """
        SELECT b.created, b.facility_id FROM bookoya_booking b
        JOIN bookoya_facility f ON f.id = b.facility_id
        WHERE f.verified IS TRUE

    """,

    'bookings_with_subscription':

    """
        SELECT b.created, b.facility_id, s.begins AS s_begin,
               s.subscription_type
        FROM bookoya_booking b
        JOIN bookoya_facility f ON f.id = b.facility_id
        INNER JOIN bookoya_monthlysubscription s ON b.facility_id = s.facility_id
        WHERE f.verified IS TRUE

    """,


}
