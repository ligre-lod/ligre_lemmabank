import { Box, Paper } from '@mui/material';
import type React from 'react';
import { useCallback, useState } from 'react';
import type { SearchFilters } from '../utils/sparql';
import Filters from './Filters';
import Results from './Results';

const Search: React.FC = () => {
  const [filters, setFilters] = useState<SearchFilters>({});

  const handleFiltersChange = useCallback((newFilters: SearchFilters) => {
    setFilters(newFilters);
  }, []);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Filters Block */}
      <Paper elevation={0}>
        <Filters onFiltersChange={handleFiltersChange} />
      </Paper>

      {/* Results List */}
      <Paper elevation={0}>
        <Results filters={filters} />
      </Paper>
    </Box>
  );
};

export default Search;
