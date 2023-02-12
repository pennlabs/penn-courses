import React from 'react';
import { NavBar } from '../styles/NavStyles';
import Logo from './NavBar/Logo';
import StateControl from './NavBar/StateControl';

const Nav = () => {
  return (
    <div className="d-flex" style={NavBar}>
      <Logo/>
      <div className='col-10 ms-4'>
        <StateControl/>
      </div>
    </div>)
}

export default Nav;