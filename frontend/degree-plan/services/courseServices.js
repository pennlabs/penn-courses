import {createApi, fetchBaseQuery} from '@reduxjs/toolkit/query/react';

export const coursesApi = createApi({
    reducerPath: "courses",
    baseQuery: fetchBaseQuery({
        baseUrl: ""
    }),
    endpoints: (builder) => ({
        getCourses: builder.query({
            query: (queryString) => {
                return ({
                    url: `/api/base/2022C/search/courses/?type=auto&search=${queryString}`,
                    method: 'GET'
                });
            },
        })
    }),
})

export const {useGetCoursesQuery} = coursesApi;
