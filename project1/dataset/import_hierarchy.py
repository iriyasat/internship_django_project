import os
import sys
import pandas as pd

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project1.settings')

import django
django.setup()

from car_sales.models import Employee, EmployeeRole, EmployeeStatus, EmployeeHierarchy, EmployeeLevel

def import_hierarchy():
    excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'employee_hierarchy_final.xlsx')
    if not os.path.exists(excel_path):
        print(f"Error: Excel file not found at {excel_path}")
        return

    print("Reading legend and populating EmployeeLevel...")
    df_legend = pd.read_excel(excel_path, sheet_name='legend')
    
    # Clear existing level records
    EmployeeLevel.objects.all().delete()
    
    level_objects = []
    unique_levels = set()
    for idx, row in df_legend.iterrows():
        lvl = int(row['Level'])
        raw_notes = str(row['Reports To']).strip()
        
        # Clean notes of symbols and layout indicators
        clean_notes = raw_notes.replace('→', '').replace('┐', '').replace('┘', '').replace('SAME LEVEL', '').strip()
        clean_notes = ' '.join(clean_notes.split())
        
        if 'TOP' in clean_notes or 'No supervisor' in clean_notes:
            formatted_notes = "Top — No supervisor"
        else:
            formatted_notes = f"Reports to {clean_notes}"
            
        if lvl not in unique_levels:
            unique_levels.add(lvl)
            level_objects.append(EmployeeLevel(level=lvl, notes=formatted_notes))
            
    EmployeeLevel.objects.bulk_create(level_objects)
    print(f"Successfully populated {len(level_objects)} levels in EmployeeLevel.")

    print(f"Reading employee hierarchy from: {excel_path}...")
    df = pd.read_excel(excel_path, sheet_name='employee_hierarchy')
    
    # Clear existing hierarchy records
    print("Clearing existing EmployeeHierarchy records...")
    EmployeeHierarchy.objects.all().delete()

    print("Beginning import of 2,000 hierarchy records...")
    hierarchy_objects = []
    
    # Pre-cache models to optimize query count
    roles = {r.role_id: r for r in EmployeeRole.objects.all()}
    levels = {l.level: l for l in EmployeeLevel.objects.all()}
    
    # Load all employees into memory for quick lookup
    employees = {e.employee_id: e for e in Employee.objects.all()}
    
    missing_employees = 0
    
    for idx, row in df.iterrows():
        emp_id = int(row['employee_id'])
        if emp_id not in employees:
            print(f"Warning: Employee with ID {emp_id} not found in DB. Skipping.")
            missing_employees += 1
            continue
            
        employee = employees[emp_id]
        role = roles.get(int(row['role_id']))
        
        # Get status from the employee's status in DB
        status = employee.status
        
        # Get matching EmployeeLevel object
        level_val = int(row['level'])
        level_obj = levels.get(level_val)
        
        # Build supervisor dict dynamically
        supervisor_kwargs = {}
        for i in range(1, 9):
            col_id = 'supervisor_id' if i == 1 else f'supervisor{i}_id'
            col_role = 'supervisor_role_id' if i == 1 else f'supervisor{i}_role_id'
            
            sup_val = row[col_id]
            role_val = row[col_role]
            
            # Field names in model
            field_sup = 'supervisor' if i == 1 else f'supervisor{i}'
            field_role = 'supervisor_role' if i == 1 else f'supervisor{i}_role'
            
            if pd.notna(sup_val):
                sup_id = int(sup_val)
                supervisor_kwargs[field_sup] = employees.get(sup_id)
            else:
                supervisor_kwargs[field_sup] = None
                
            if pd.notna(role_val):
                r_id = int(role_val)
                supervisor_kwargs[field_role] = roles.get(r_id)
            else:
                supervisor_kwargs[field_role] = None
                
        hierarchy_obj = EmployeeHierarchy(
            employee=employee,
            role=role,
            level=level_obj,
            status=status,
            **supervisor_kwargs
        )
        hierarchy_objects.append(hierarchy_obj)

    print(f"Bulk inserting {len(hierarchy_objects)} hierarchy records...")
    EmployeeHierarchy.objects.bulk_create(hierarchy_objects)
    print("Bulk insert finished successfully!")
    if missing_employees > 0:
        print(f"Skipped {missing_employees} records because the corresponding employee was missing in DB.")

if __name__ == '__main__':
    import_hierarchy()
