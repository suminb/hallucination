require 'test_helper'

class ProxiesControllerTest < ActionController::TestCase
  setup do
    @proxy = proxies(:one)
  end

  test "should get index" do
    get :index
    assert_response :success
    assert_not_nil assigns(:proxies)
  end

  test "should get new" do
    get :new
    assert_response :success
  end

  test "should create proxy" do
    assert_difference('Proxy.count') do
      post :create, :proxy => @proxy.attributes
    end

    assert_redirected_to proxy_path(assigns(:proxy))
  end

  test "should show proxy" do
    get :show, :id => @proxy.to_param
    assert_response :success
  end

  test "should get edit" do
    get :edit, :id => @proxy.to_param
    assert_response :success
  end

  test "should update proxy" do
    put :update, :id => @proxy.to_param, :proxy => @proxy.attributes
    assert_redirected_to proxy_path(assigns(:proxy))
  end

  test "should destroy proxy" do
    assert_difference('Proxy.count', -1) do
      delete :destroy, :id => @proxy.to_param
    end

    assert_redirected_to proxies_path
  end
end
