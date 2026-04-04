import React from 'react';
import styled from 'styled-components';
import RangeSlider from 'react-range-slider-input';
import 'react-range-slider-input/dist/style.css';

const Container = styled.div`
    display: flex;
    padding: 24px 12px 0 12px;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    align-self: stretch;

    /* The main background track */
    .range-slider {
        background: #EFF1F5; 
        height: 6px;
        border-radius: 10px;
    }

    /* The filled-in colored part between the thumbs */
    .range-slider__range {
        background: #3E3E40; 
    }

    .range-slider__thumb {
        background: transparent;
        border: none;
        width: 18px;
        height: 18px;
        pointer-events: auto; 
    }

    /* the pseudo-element inside the thumb. */
    .range-slider__thumb::after {
        content: '';
        display: flex;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background: #FFFFFF;
        border: 2px solid #D9D9D9;
        transition: transform 0.1s;
        transform: scale(1);
        transform: translate(0%, -10%);
    }

    .range-slider__thumb[data-active]::after {
        transform: scale(1.2) translate(0%, -10%);
    }

`;

const RangeMarkers = styled.div`
    display: flex;
    justify-content: space-between;
    align-items: center;
    align-self: stretch;
    font-size: 12px;
    font-family: 'SFPro', sans-serif;
    font-weight: 700;
    margin: 15px 6% 0 6%;
`;

const SliderSelect = ({ ratingValues, setRatingValues }) => {
    return (
        <div style={{width: '100%', userSelect: 'none', WebkitUserSelect: 'none', MozUserSelect: 'none', maxWidth: '400px'}}>
            <Container>
                <RangeSlider 
                    min={1}
                    max={4}
                    step={1}
                    value={ratingValues}
                    onInput={(value) => {
                        setRatingValues(value);
                    }}
                />  
            </Container>
            <RangeMarkers>
                <div>1</div>
                <div>2</div>
                <div>3</div>
                <div>4</div>
            </RangeMarkers>
            <RangeMarkers style={{color: '#A1A1A1', marginTop: '5px'}}>
                <div>Poor</div>
                <div>Excellent</div>
            </RangeMarkers>
        </div>
    )
}

export default SliderSelect;