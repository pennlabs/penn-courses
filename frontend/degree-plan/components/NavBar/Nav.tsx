import React from 'react';
import { NavBar } from '../../styles/NavStyles';
import Logo from './Logo';
import { user } from '../../data/user';

const Nav = () => {
  const nameString = `${user.firstName} ${user.lastName}`
  return (
    <div className="d-flex justify-content-between" style={NavBar}>
      <Logo/>
      {/* <Link to="" className='text-dark text-decoration-none'> */}
        <h3 className='mt-3'>{nameString}</h3>
      {/* </Link> */}
    </div>)
}

export default Nav;