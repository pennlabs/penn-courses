import React from "react";
import { CartPanel } from "../../styles/CartStyles";
import CurrentCartContent from "./CurrentCartContent";
import CurrentCartTitle from "./CurrentCartTitle";
import AllCarts from "./AllCarts";
import CreateNewCart from "./CreateNewCart";

const Cart = () => {

  return (
    <div className='mt-4' style={CartPanel}>
      <CurrentCartTitle />
      <CurrentCartContent />
      <AllCarts />
      <CreateNewCart />
    </div>)
}

export default Cart;
