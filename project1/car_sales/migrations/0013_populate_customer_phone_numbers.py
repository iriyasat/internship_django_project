from django.db import migrations

def format_phone(cid, cname):
    # Hash cid to get 8 pseudo-random digits
    h = (cid * 2654435761) % (10**8)
    h_str = f'{h:08d}'
    
    if cname == 'Australia':
        return f'+61 4{h_str[:2]} {h_str[2:5]} {h_str[5:8]}'
    elif cname == 'Brazil':
        return f'+55 11 9{h_str[:4]}-{h_str[4:8]}'
    elif cname == 'Canada':
        area = (cid * 17) % 800 + 100
        return f'+1 {area}-555-{h_str[4:8]}'
    elif cname == 'China':
        return f'+86 138 {h_str[:4]} {h_str[4:8]}'
    elif cname == 'France':
        return f'+33 6 {h_str[:2]} {h_str[2:4]} {h_str[4:6]} {h_str[6:8]}'
    elif cname == 'Germany':
        return f'+49 151 {h_str[:4]}{h_str[4:8]}'
    elif cname == 'India':
        return f'+91 9{h_str[:4]} {h_str[4:8]}{(cid*3)%10}'
    elif cname == 'Italy':
        return f'+39 3{h_str[:2]} {h_str[2:8]}'
    elif cname == 'Japan':
        return f'+81 90 {h_str[:4]} {h_str[4:8]}'
    elif cname == 'Mexico':
        return f'+52 55 {h_str[:4]} {h_str[4:8]}'
    elif cname == 'Netherlands':
        return f'+31 6 {h_str[:8]}'
    elif cname == 'New Zealand':
        return f'+64 21 {h_str[:3]} {h_str[3:7]}'
    elif cname == 'Saudi Arabia':
        return f'+966 50 {h_str[:3]} {h_str[3:7]}'
    elif cname == 'Singapore':
        return f'+65 9{h_str[:3]} {h_str[3:7]}'
    elif cname == 'South Africa':
        return f'+27 82 {h_str[:3]} {h_str[3:7]}'
    elif cname == 'South Korea':
        return f'+82 10 {h_str[:4]} {h_str[4:8]}'
    elif cname == 'Spain':
        return f'+34 6{h_str[:2]} {h_str[2:4]} {h_str[4:6]} {h_str[6:8]}'
    elif cname == 'United Arab Emirates':
        return f'+971 50 {h_str[:3]} {h_str[3:7]}'
    elif cname == 'United Kingdom':
        return f'+44 7{h_str[:3]} {h_str[3:8]}'
    elif cname == 'United States':
        area = (cid * 31) % 800 + 100
        return f'+1 {area}-555-{h_str[4:8]}'
    else:
        return f'+1 555-01{h_str[4:6]}'


def populate_customer_phones(apps, schema_editor):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT ci.customer_id, co.country_name
            FROM customer_info ci
            JOIN country co ON ci.country_id = co.country_id;
        ''')
        rows = cursor.fetchall()
        
        updates = []
        for cid, cname in rows:
            phone = format_phone(cid, cname)
            updates.append((phone, cid))
        
        # Execute in batches for fast bulk update
        cursor.executemany('''
            UPDATE customer SET phone = %s WHERE customer_id = %s;
        ''', updates)


def reverse_customer_phones(apps, schema_editor):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("UPDATE customer SET phone = NULL;")


class Migration(migrations.Migration):

    dependencies = [
        ('car_sales', '0012_customer_split_and_profile_picture'),
    ]

    operations = [
        migrations.RunPython(populate_customer_phones, reverse_code=reverse_customer_phones),
    ]
