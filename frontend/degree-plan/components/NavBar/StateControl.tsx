import { TypedUseSelectorHook, useSelector, useDispatch} from 'react-redux';
import React from 'react';
import { showCartSet } from '../../store/reducers/nav';
import { showFourYearPlanSet } from '../../store/reducers/nav';
import { navButtonOn, navButtonOff, fourYearButtonOff } from '../../styles/NavStyles';
import { Link } from "react-router-dom";
import { checkOutPageSet } from '../../store/reducers/nav';
import { AppDispatch } from '../../store/configureStore';
import { RootState } from '../../store/configureStore';

export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

const StateControl = () => {
    const toggleFourYearPlan = () => {
        dispatch(showFourYearPlanSet(!!data && query));
    }
    const toggleCart = () => {
        dispatch(showCartSet());
    }
    const handleBack = () => {
        dispatch(checkOutPageSet(false));
    }
    
    const data = useSelector((store : RootState) => store.entities.courses);
    const showCart = useSelector((store : RootState) => store.nav.showCart);
    const onContentPage = useSelector((store : RootState) => store.nav.onContentPage);
    const showFourYearPlan = useSelector((store : RootState) => store.nav.showFourYearPlan);
    const query = useSelector((store : RootState) => store.search.queryString);
    const onCheckoutPage = useSelector((store : RootState) => store.nav.onCheckoutPage);
    const cartButtonContent = showCart ? 'Hide Cart' : 'Show Cart';
    const fourYearButtonContent = !showFourYearPlan ? '4 Year Plan' : 'Back'
    const dispatch = useDispatch();

    return (
        <div className='d-flex justify-content-between col-12'>
            {!onCheckoutPage && 
                <button style={showFourYearPlan ? navButtonOn : fourYearButtonOff} 
                        className='m-2 btn btn-outline-secondary' 
                        onClick={toggleFourYearPlan}> 
                    {fourYearButtonContent}
                </button>}
            <div>
                {onContentPage && !onCheckoutPage && 
                    <button style={showCart ? navButtonOn : navButtonOff} 
                            className="m-2 btn btn-outline-secondary" 
                            onClick={toggleCart}> 
                        {cartButtonContent}
                    </button>}
                

                {onCheckoutPage &&
                    <Link to='/'>
                        <button style={navButtonOn} 
                                className='m-2 btn btn-outline-secondary'
                                onClick={handleBack}> 
                            Back
                        </button>
                    </Link>}
            </div>
      </div>
    )
}

export default StateControl;