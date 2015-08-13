QUERIES = {
    'active_verified_facilities':

    """
        SELECT b.created, f.id AS facility_id, f.created AS f_created
        FROM bookoya_booking b
        FULL OUTER JOIN bookoya_facility f ON f.id = b.facility_id
        WHERE f.verified IS TRUE

    """,
}
