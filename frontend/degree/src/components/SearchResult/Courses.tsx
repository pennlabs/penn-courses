
import React from 'react';
import Detail from './Detail';
import {useSelector} from 'react-redux';
import Course from './Course';
import { searchResult } from '../../styles/SearchResultStyles';
import { RootState, ICourse } from '../../store/configureStore';

const Courses = () => {

  const courses = useSelector((store : RootState) => store.entities.courses);
  const showCart = useSelector((store : RootState) => store.nav.showCart);
  const current = useSelector((store : RootState) => store.entities.current);

  return (
    <>
      {!!courses &&
      <div className={`${current.id ? 'col-3' : 'col-5'} mt-4 me-4`}>
        <ul className="list-group" style={searchResult}>
          {courses.map((course : ICourse) => (
            <Course course={course}/>
          ))}
        </ul>
      </div>}
      
      {current.id && 
          <div className={showCart ? 'col-5' : 'col-6'}>
            <Detail />
          </div>
      }
    </>
    
    )
}

export default Courses;