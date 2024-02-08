import React from 'react';
import { navButtonOn, navButtonOff, fourYearButtonOff } from '../../styles/NavStyles';
import { Link } from "react-router-dom";

const StateControl = () => {
    const toggleFourYearPlan = () => {}
    const toggleCart = () => {}
    const handleBack = () => {}
    
    const data = [];
    const showCart = false;
    const onContentPage = false;
    const showFourYearPlan = false;
    const query = "";
    const onCheckoutPage = false;
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