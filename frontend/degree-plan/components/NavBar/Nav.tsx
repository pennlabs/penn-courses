import React from 'react';
import { NavBar } from '../../styles/NavStyles';
import Logo from './Logo';
import { user } from '../../data/user';

const Nav = () => {
  const nameString = `${user.firstName} ${user.lastName}`
  return (
    <div className="d-flex justify-content-between" style={NavBar}>
      <Logo/>
      <div style={{color: '#000000', fontSize: '23px'}} className='mt-3 me-4'>{nameString}</div>
    </div>)
}

export default Nav;