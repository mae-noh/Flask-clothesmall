import os
from flask import render_template, request, session, Flask, g, redirect, flash, json, jsonify

from ..database import DBManager
from ..model.product import Product
from ..model.productcategory import ProductCategory
from ..controller.login import login_required
from ..clothesmall_blueprint import clothesmall


#ping
@clothesmall.route('/ping', methods=['GET'])
def ping():
    return jsonify('pong!')

@clothesmall.route('/')
def main():
    '''메인 페이지'''
    print('*'*100)
    print("main print")

    loginargs = request.args.get('islogin')
    category = __get_category_all()

    print('-- islogin', loginargs)
    return render_template('layout.html', islogin = loginargs, categories = category)

def __get_product_all():
    '''상품 전체목록을 가져온다.'''
    try:
        products = g.db.query(Product).filter(Product.is_deleted==0).order_by(Product.id)
        return products 
     
    except Exception as e:
        print('error message',e)
        raise e

def __get_category_all():
    '''상품 카테고리 목록을 가져온다.'''
    try:
        categories = g.db.query(ProductCategory).order_by(ProductCategory.id)
        return categories
     
    except Exception as e:
        print('error message',e)
        raise e


@clothesmall.route('/product/list')
def read_product_all():
    '''상품 전체 목록'''
    products = __get_product_all()
    category = __get_category_all()
    return render_template('product.html', data = products, categories = category)

def __get_products_category(id):
    '''선택된 카테고리 상품목록을 가져온다.'''
    try:
        products = g.db.query(Product).filter(Product.product_category == id).all()
        return products
     
    except Exception as e:
        print('error message',e)
        raise e

@clothesmall.route('/product/list/<id>')
def read_product_selected(id):
    '''선택된 카테고리 상품 보여주기'''
    products = __get_products_category(id)
    category = __get_category_all()

    return render_template('product.html', data = products, categories = category)

def __create_product(name, cost_price, selling_price, admin_id, product_category, is_deleted, img_address, product_information): 
    '''새로운 상품을 등록한다.'''  
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

@clothesmall.route('/product/register')
@login_required
def register_product_form():
    '''상품 등록 폼'''
    category = __get_category_all()

    #TODO : 유효성체크 함수 만들기
    print('::::: visited /product/register | register_product_form()')
    return render_template('editproduct.html', categories = category)

@clothesmall.route('/product/register', methods=['POST'])
def register_product():
    '''사용자 등록'''

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
    '''일치하는 id의 상품을 가져온다.'''
    try:
        product = g.db.query(Product).filter_by(id=id).one()
        return product 
     
    except Exception as e:
        print(str(e))
        raise e

@clothesmall.route('/product/detail/<id>')
def read_product_detail(id):
    '''상품 상세 페이지'''
    print('************* 상품 아이디', id)
    product = __get_product_one(id)
    category = __get_category_all()

    return render_template('productdetail.html', data = product, categories = category)

@clothesmall.route('/product/editform', methods=['POST'])
@login_required
def modify_product_form():
    '''상품 수정을 위한 폼을 제공하는 함수'''
    #TODO : 유효성체크 함수 만들기
    id = request.form.get('product_id')
    product = __get_product_one(id)
    category = __get_category_all()

    return render_template('editproduct.html', data = product, categories = category)

def __modify_product_(id, name, cost_price, selling_price, product_category):
    '''선택된 id의 상품을 수정한다. update'''
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


@clothesmall.route('/product/edit', methods=['POST'])
@login_required
def modify_product():
    '''상품 수정'''
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
    '''일치하는 id의 상품의 is_deleted 상태를 1로 변경한다.'''
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

@clothesmall.route('/product/delete', methods=['POST'])
@login_required
def remove_product():
    '''상품 삭제'''
    id = request.form.get('product_id')
    print('remove_product:::::::::::', id)
    __delete_product(id)
    return redirect('/product/list')
