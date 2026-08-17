import { ContentCopy } from '@mui/icons-material';
import { Box, Button, Divider, Typography } from '@mui/material';
import type React from 'react';
import { useEffect, useState } from 'react';
import type { SearchFilters } from '../utils/sparql';
import {
  generateSparqlQuery,
  getGenderOptions,
  getInflectionOptions,
  getPosOptions,
} from '../utils/sparql';
import FilterRegexp from './FilterRegexp';
import FilterSelect from './FilterSelect';

interface FiltersProps {
  onFiltersChange: (filters: SearchFilters) => void;
}

const Filters: React.FC<FiltersProps> = ({ onFiltersChange }) => {
  const [lemma, setLemma] = useState<string>('');
  const [inflectionType, setInflectionType] = useState<string>('');
  const [pos, setPos] = useState<string>('');
  const [gender, setGender] = useState<string>('');

  // Notify parent component when filters change
  useEffect(() => {
    const filters: SearchFilters = {
      lemma: lemma || undefined,
      inflectionType: inflectionType || undefined,
      pos: pos || undefined,
      gender: gender || undefined,
    };
    onFiltersChange(filters);
  }, [lemma, inflectionType, pos, gender, onFiltersChange]);

  const getSparqlQuery = () => {
    const filters: SearchFilters = {
      lemma: lemma || undefined,
      inflectionType: inflectionType || undefined,
      pos: pos || undefined,
      gender: gender || undefined,
    };
    return generateSparqlQuery(filters);
  };

  const handleCopySparql = async () => {
    try {
      await navigator.clipboard.writeText(getSparqlQuery());
    } catch (error) {
      console.error('Failed to copy SPARQL query:', error);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
        }}
      >
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Search Filters
        </Typography>
        <Button
          variant="outlined"
          size="small"
          startIcon={<ContentCopy />}
          onClick={handleCopySparql}
          disabled={!lemma && !inflectionType && !pos && !gender}
          sx={{ fontSize: '0.75rem', py: 0.5 }}
        >
          copy sparql query
        </Button>
      </Box>
      <Divider sx={{ mb: 3 }} />

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 2,
        }}
      >
        <FilterRegexp
          label="Lemma (regexp)"
          value={lemma}
          onChange={setLemma}
        />

        <FilterSelect
          label="Inflection Type"
          value={inflectionType}
          fetchOptions={getInflectionOptions}
          onChange={setInflectionType}
        />

        <FilterSelect
          label="POS"
          value={pos}
          fetchOptions={getPosOptions}
          onChange={setPos}
        />

        <FilterSelect
          label="Gender"
          value={gender}
          fetchOptions={getGenderOptions}
          onChange={setGender}
        />
      </Box>
    </Box>
  );
};

export default Filters;
