import useSWR from "swr";

const fetcher = (url) => fetch(url).then((res) => res.json());
const url = "/api/options/";

export default function useOption(key) {
    const { data, error } = useSWR(url, fetcher);
    if (!error && data && data[key]) {
        console.log(data[key]);
        return data[key];
    }
}
