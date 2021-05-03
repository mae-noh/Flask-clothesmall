import os
from flask import Blueprint
from flask import render_template, request, session, Flask, g, redirect, flash

from ..database import DBManager
from ..model.product import Product
from ..model.productcategory import ProductCategory
from ..controller.login import login_required


bp = Blueprint('product', __name__, url_prefix='/')

@bp.before_request
def get_db():
    '''Connects to the specific database.'''
    # 데이터베이스 처리
    
    DBManager.init('postgresql://mae:mae1234@localhost:5432/postgres', False) #DB매니저 클래스 초기화
    DBManager.init_db()
    print('get_db',g.db)

def __get_product_all():
    '''상품목록 가져오기'''
    try:
        products = g.db.query(Product).filter(Product.is_deleted==0).order_by(Product.id)
        return products 
     
    except Exception as e:
        print('error message',e)
        raise e

def __get_category_all():
    '''상품 카테고리 가져오기'''
    try:
        categories = g.db.query(ProductCategory).order_by(ProductCategory.id)
        return categories
     
    except Exception as e:
        print('error message',e)
        raise e

@bp.route('/')
def main():
    print("-- main print")
    loginargs = request.args.get('islogin')
    category = __get_category_all()
    print('-- islogin', loginargs)
    return render_template('layout.html', islogin = loginargs, categories = category)

@bp.route('/product/list')
def read_product_all():
    products = __get_product_all()
    category = __get_category_all()
    return render_template('product.html', data = products, categories = category)

def __get_products_category(id):
    '''선택된 카테고리 상품 가져오기'''
    try:
        products = g.db.query(Product).filter(Product.product_category == id).all()
        return products
     
    except Exception as e:
        print('error message',e)
        raise e

@bp.route('/product/list/<id>')
def read_product_selected(id):
    products = __get_products_category(id)
    category = __get_category_all()

    return render_template('product.html', data = products, categories = category)

def __create_product(name, cost_price, selling_price, admin_id, product_category, is_deleted, img_address, product_information):   
    try:
        product = Product(name, cost_price, selling_price, admin_id, product_category, is_deleted, img_address, product_information)
        g.db.add(product)
        g.db.commit()
        flash('상품 등록이 완료되었습니다.')
        
    except Exception as e:
        error = "DB error occurs : " + str(e)
        print(error)
        g.db.rollback()
        flash('상품 등록이 실패했습니다.')
        raise e

@bp.route('/product/register')
@login_required
def register_product_form():
    '''상품 등록을 위한 폼을 제공하는 함수'''
    category = __get_category_all()

    #TODO : 유효성체크 함수 만들기
    print('::::: visited /product/register | register_product_form()')
    return render_template('editproduct.html', categories = category)

@bp.route('/product/register', methods=['POST'])
def register_product():
    '''사용자 등록을 위한 함수'''

    try:
        name = request.form['pname']
        cost_price = request.form['cost_price']
        selling_price = request.form['selling_price']
        admin_id = 1
        product_category = request.form['category']
        is_deleted = 0
        img_address = 'basic.jpg'
        product_information = "상품 상세 정보"

        if not name:
            error = '상품명이 없습니다.'
        elif not cost_price:
            error = '원가가 없습니다.'
        elif not selling_price:
            error = '판매가가 없습니다.'
        elif not product_category:
            error = '카테고리가 없습니다.'
        else:
            __create_product(name, cost_price, selling_price, admin_id, product_category, is_deleted, img_address, product_information)
        
    except Exception as e:
        error = "DB error occurs : " + str(e)
        print(error)
        g.db.rollback()
        flash('상품 등록이 실패했습니다.')
        raise e

    return redirect('/product/list')
    
def __get_product_one(id):
    try:
        product = g.db.query(Product).filter_by(id=id).one()
        return product 
     
    except Exception as e:
        print(str(e))
        raise e

@bp.route('/product/detail/<id>')
def read_product_detail(id):
    '''상품 상세 페이지'''
    print('************* 상품 아이디', id)
    product = __get_product_one(id)
    category = __get_category_all()

    return render_template('productdetail.html', data = product, categories = category)

@bp.route('/product/editform', methods=['POST'])
@login_required
def modify_product_form():
    '''상품 수정을 위한 폼을 제공하는 함수'''
    #TODO : 유효성체크 함수 만들기
    id = request.form.get('product_id')
    product = __get_product_one(id)
    category = __get_category_all()

    return render_template('editproduct.html', data = product, categories = category)

def __modify_product_(id, name, cost_price, selling_price, product_category):
    try:
        g.db.query(Product).filter_by(id=id).update({'name':name, 'cost_price':cost_price, 'selling_price':selling_price, 'product_category':product_category})
        g.db.commit()
        print('상품 수정이 성공했습니다.')
     
    except Exception as e:
        error = "DB error occurs : " + str(e)
        print(error)
        g.db.rollback()
        print('상품 수정이 실패했습니다.')
        raise e


@bp.route('/product/edit', methods=['POST'])
@login_required
def modify_product():
    '''상품목록 수정하기'''
    try:
        id = request.form['product_id']
        name = request.form['pname']
        cost_price = request.form['cost_price']
        selling_price = request.form['selling_price']
        product_category = request.form['category']

        if not id:
            error = '상품번호가 없습니다.'
        elif not name:
            error = '상품명이 없습니다.'
        elif not cost_price:
            error = '원가가 없습니다.'
        elif not selling_price:
            error = '판매가가 없습니다.'
        elif not product_category:
            error = '카테고리가 없습니다.'
        else:
            __modify_product_(id, name, cost_price, selling_price, product_category)

    except Exception as e:
        print('error message',e)
        raise e

    return redirect('/product/list')

def __delete_product(id):
    try:
        product = g.db.query(Product).filter_by(id=id).first()
        print('delete::::::::::::', product)
        product.is_deleted = 1
        g.db.commit()
        print('상품 삭제를 성공했습니다.')
     
    except Exception as e:
        error = "DB error occurs : " + str(e)
        print(error)
        g.db.rollback()
        print('상품 삭제하는데 실패했습니다.')
        raise e

@bp.route('/product/delete', methods=['POST'])
@login_required
def remove_product():
    '''상품삭제하기'''
    id = request.form.get('product_id')
    print('remove_product:::::::::::', id)
    __delete_product(id)
    return redirect('/product/list')
