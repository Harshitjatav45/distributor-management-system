import MasterDataPage from './MasterDataPage';

const fields = [
  { name: 'category_name', label: 'Category Name', type: 'text', required: true },
  { name: 'category_code', label: 'Category Code', type: 'text' },
  { name: 'description', label: 'Description', type: 'textarea' },
  { name: 'is_active', label: 'Active', type: 'checkbox' },
];

const listColumns = [
  { key: 'category_name', header: 'Category Name' },
  { key: 'category_code', header: 'Code' },
];

export default function Categories() {
  return (
    <MasterDataPage
      title="Categories"
      apiPath="/category/"
      fields={fields}
      listColumns={listColumns}
      searchFields={['category_name', 'category_code']}
    />
  );
}
