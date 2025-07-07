#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug script to test different connect_args configurations
"""

from sqlalchemy import create_engine, text

def test_connect_args_configurations():
    print('🔍 CONNECT_ARGS SPECIFIC TESTING')

    # Test different connect_args configurations
    configurations = [
        ('No connect_args', {}),
        ('Only client_encoding utf8', {'client_encoding': 'utf8'}),
        ('Only client_encoding UTF8', {'client_encoding': 'UTF8'}),
        ('Only timezone', {'options': '-c timezone=Europe/Budapest'}),
        ('Both (current config)', {
            'client_encoding': 'utf8',
            'options': '-c timezone=Europe/Budapest'
        }),
        ('UTF8 uppercase + timezone', {
            'client_encoding': 'UTF8',
            'options': '-c timezone=Europe/Budapest'  
        }),
        ('Different timezone', {'options': '-c timezone=UTC'}),
        ('Complex options', {'options': '-c timezone=Europe/Budapest -c client_encoding=utf8'}),
    ]

    base_url = 'postgresql://lambda_user:Cz31n1ng3r@localhost:5432/lambda_db'

    for desc, connect_args in configurations:
        print(f'\n{desc}:')
        print(f'   connect_args: {connect_args}')
        
        try:
            engine = create_engine(base_url, connect_args=connect_args)
            print('   ✅ Engine creation successful')
            
            # Test connection
            conn = engine.connect()
            result = conn.execute(text('SELECT 1 as test'))
            test_val = result.fetchone()[0]
            print(f'   ✅ Connection successful, result: {test_val}')
            conn.close()
            
        except Exception as e:
            print(f'   ❌ Failed: {e}')
            if 'position 66' in str(e) and '0xe1' in str(e):
                print(f'   🚨 UTF-8 ERROR WITH THIS CONFIG!')
                print(f'   This configuration causes the position 66 error!')
                
                # Analyze which specific setting causes the issue
                if 'client_encoding' in connect_args:
                    encoding_val = connect_args['client_encoding']
                    print(f'   💡 client_encoding might be the problem: {encoding_val}')
                if 'options' in connect_args:
                    options_val = connect_args['options']
                    print(f'   💡 options might be the problem: {options_val}')
            else:
                error_preview = str(e)[:100]
                print(f'   💡 Different error (not position 66): {error_preview}...')

if __name__ == "__main__":
    test_connect_args_configurations() 