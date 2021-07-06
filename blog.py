import sqlite3
import sys
import argparse


def execute_query(connection, query, dct=None):
    if dct is None:
        dct = []
    cur = connection.cursor()
    r = cur.execute(query, dct)
    connection.commit()
    return r


parser = argparse.ArgumentParser()
parser.add_argument('File')
parser.add_argument('--ingredients')
parser.add_argument('--meals')
name = sys.argv[1]
args = parser.parse_args()
con = sqlite3.connect(name)
data = {"meals": ("breakfast", "brunch", "lunch", "supper"),
        "ingredients": ("milk", "cacao", "strawberry", "blueberry", "blackberry", "sugar"),
        "measures": ("ml", "g", "l", "cup", "tbsp", "tsp", "dsp", "")}

create_measures = '''
CREATE TABLE IF NOT EXISTS measures (
    measure_id INTEGER PRIMARY KEY AUTOINCREMENT,
    measure_name TEXT UNIQUE
);
'''
create_ingredients = '''
CREATE TABLE IF NOT EXISTS ingredients (
    ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_name TEXT NOT NULL UNIQUE
);
'''
create_meals = '''
CREATE TABLE IF NOT EXISTS meals (
    meal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_name TEXT NOT NULL UNIQUE
);
'''
create_recipes = '''
CREATE TABLE IF NOT EXISTS recipes (
    recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_name TEXT NOT NULL,
    recipe_description TEXT
);
'''
create_serve = '''
CREATE TABLE IF NOT EXISTS serve (
    serve_id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    FOREIGN KEY(meal_id) REFERENCES meals (meal_id) FOREIGN KEY(recipe_id) REFERENCES recipes (recipe_id)
);
'''
create_quantity = '''
CREATE TABLE IF NOT EXISTS quantity (
    quantity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    quantity INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    measure_id INTEGER NOT NULL,
    ingredient_id INTEGER NOT NULL,
    FOREIGN KEY(recipe_id) REFERENCES recipes (recipe_id) FOREIGN KEY(measure_id) REFERENCES measures (measure_id)
    FOREIGN KEY(ingredient_id) REFERENCES ingredients (ingredient_id)
);
'''
execute_query(con, 'PRAGMA foreign_keys = ON;')
execute_query(con, create_measures)
execute_query(con, create_ingredients)
execute_query(con, create_meals)
execute_query(con, create_recipes)
execute_query(con, create_serve)
execute_query(con, create_quantity)

for table in data:
    column = table[:-1] + '_name'
    for i in range(len(data[table])):
        ins = f'''
        INSERT OR IGNORE INTO
            {table} ({column})
        VALUES 
            ('{data[table][i]}');
        '''
        execute_query(con, ins)
if args.ingredients is None and args.meals is None:
    while True:
        print('Pass the empty recipe name to exit.')
        name = input('Recipe name: ')
        if name == '':
            break
        desc = input('Recipe description: ')
        ins = f'''
        INSERT INTO
            recipes (recipe_name, recipe_description)
        VALUES 
            ('{name}', '{desc}');
        '''
        recipe_id = execute_query(con, ins).lastrowid
        print('1) breakfast  2) brunch  3) lunch  4) supper ')
        meals = list(map(int, input('When the dish can be served: ').split()))
        for meal_id in meals:
            ins = f'''
            INSERT INTO
                serve (meal_id, recipe_id)
            VALUES
                ('{meal_id}', '{recipe_id}')
            '''
            execute_query(con, ins)
        while True:
            mean = input('Input quantity of ingredient <press enter to stop>: ').split()
            if not mean:
                break
            quantity = int(mean[0])
            if len(mean) == 2:
                measure = 8
                ins = f"SELECT ingredient_id FROM ingredients WHERE ingredient_name LIKE '{mean[1]}%'"
                all_ing = execute_query(con, ins).fetchall()
                if len(all_ing) == 1:
                    ingredient = all_ing[0][0]
                else:
                    print('The ingredient is not conclusive!')
                    continue
            else:
                ins = f"SELECT measure_id FROM measures WHERE measure_name LIKE '{mean[1]}%'"
                all_meas = execute_query(con, ins).fetchall()
                if len(all_meas) == 1:
                    measure = all_meas[0][0]
                else:
                    print('The measure is not conclusive!')
                    continue
                ins = f"SELECT ingredient_id FROM ingredients WHERE ingredient_name LIKE '{mean[2]}%'"
                all_ing = execute_query(con, ins).fetchall()
                if len(all_ing) == 1:
                    ingredient = all_ing[0][0]
                else:
                    print('The ingredient is not conclusive!')
                    continue
            ins = f'''
            INSERT INTO 
                quantity (quantity, recipe_id, measure_id, ingredient_id)
            VALUES
                ('{quantity}', '{recipe_id}', '{measure}', '{ingredient}');
            '''
            execute_query(con, ins)
else:
    ingredient = args.ingredients.split(',')
    for x in ingredient:
        if x not in data['ingredients']:
            print('There are no such recipes in the database.')
            con.close()
            exit()
    ins = f'''
        SELECT 
            ingredient_id
        FROM
            ingredients
        WHERE
            ingredient_name IN ({','.join(['?'] * len(ingredient))});
        '''
    ingr = execute_query(con, ins, ingredient).fetchall()
    meals = args.meals.split(',')
    ins = f'''
            SELECT 
                meal_id
            FROM
                meals
            WHERE
                meal_name IN ({','.join(['?'] * len(meals))});
            '''
    meal = ','.join([str(x[0]) for x in execute_query(con, ins, meals).fetchall()])
    set_1 = set()
    for index, ing in enumerate(ingr):
        search = f'''
        SELECT
            recipe_id
        FROM
            quantity
        WHERE
            ingredient_id = {ing[0]};
        '''
        if index == 0:
            for el in execute_query(con, search).fetchall():
                set_1.add(el[0])
        else:
            set_2 = set()
            for el in execute_query(con, search).fetchall():
                set_2.add(el[0])
            set_1 &= set_2
    for k in set_1:
        check = f'''
        SELECT
            meal_id IN ({meal}) 
        FROM 
            serve 
        WHERE 
            recipe_id = {k}; 
        '''
        if (1,) not in execute_query(con, check).fetchall():
            set_1.remove(k)
    final = f'''
    SELECT
        recipe_name
    FROM 
        recipes
    WHERE
        recipe_id IN ({','.join([str(x) for x in set_1])});
    '''
    prod = ', '.join([x[0] for x in execute_query(con, final).fetchall()])
    print(prod if len(prod) > 0 else 'There are no such recipes in the database.')
con.close()
