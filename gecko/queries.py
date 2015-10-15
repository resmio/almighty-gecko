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
        SELECT b.created, b.facility_id, b.source, b.num FROM bookoya_booking b
        JOIN bookoya_facility f ON f.id = b.facility_id
        WHERE f.verified IS TRUE

    """,

    'bookings_with_subscription':

    """
        SELECT b.created, b.facility_id, s.begins AS s_begin,
               s.subscription_type
        FROM bookoya_booking b
        JOIN bookoya_facility f ON f.id = b.facility_id
        JOIN bookoya_monthlysubscription s
        ON f.active_plan_id = s.id
        WHERE f.verified IS TRUE

    """,

    'facilities_with_subscription':

    """
        SELECT f.id, f.created, s.subscription_type, s.begins, s.ends
        FROM bookoya_facility f
        JOIN bookoya_monthlysubscription s ON f.id = s.facility_id
        WHERE f.verified IS TRUE

    """,

}
