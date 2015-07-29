QUERIES = {

    'number_facilities':

    """
        SELECT * FROM bookoya_facility f
        WHERE f.verified IS TRUE

    """,

    'number_bookings':

    """
        SELECT b.created FROM bookoya_booking b
        JOIN bookoya_facility f ON f.id = b.facility_id
        WHERE f.verified IS TRUE

    """,
}
