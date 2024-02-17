import { useState } from 'react';
import QObject from './QObject';
import { Rule } from '@/types';
import styled from '@emotion/styled';
import { Icon } from '../bulma_derived_components';

const RuleTitle = styled.div`
    font-size: 1rem;
    font-weight: 500;
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    background-color: var(--primary-color-light);
    color: #575757;
    padding: 0.25rem .5rem;
    margin: 0.5rem 0;
    border-radius: .5rem;
`

const CourseRequirementWrapper = styled.div`
  margin: .5rem;
  margin-left: 0;
  display: flex;
  justify-content: space-between;
  gap: .5rem;
  align-items: center;
`

const CusCourses = styled.div`
  font-weight: 500;
  font-size: .9rem;
  white-space: nowrap;
`

interface RuleProps {
    rule: Rule;
    setSearchClosed: any;
    handleSearch: any;
}

/**
 * Recursive component to represent a rule.
 * @returns 
 */
const Rule = ({ rule, setSearchClosed, handleSearch } : RuleProps) => {
    const [collapsed, setCollapsed] = useState(false);
    return (
      <>
        {rule.q ? 
          <CourseRequirementWrapper>
              <QObject q={rule.q} reqId={rule.id} handleSearch={handleSearch}/>
              {rule.credits && <CusCourses>{rule.credits} cus</CusCourses>}
              {rule.num && <CusCourses>{rule.num} courses</CusCourses>}
          </CourseRequirementWrapper>
          :
          <RuleTitle onClick={() => setCollapsed(!collapsed)}>
            <div>{rule.title}</div>
            {rule.rules.length && 
                <Icon>
                  <i className={`fas fa-chevron-${collapsed ? "up" : "down"}`}></i>
                </Icon>
            }
          </RuleTitle>
          }

        {!collapsed && <div className="ms-3">
            {rule.rules.map((rule: any, index: number) => 
                <Rule key={rule.id} rule={rule} setSearchClosed={setSearchClosed} handleSearch={handleSearch} />
            )}
          </div>
          }
      </>
    )
}

export default Rule;