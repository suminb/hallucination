class CreateProxies < ActiveRecord::Migration
  def self.up
    create_table :proxies do |t|
      t.string :ip
      t.integer :port
      t.string :country

      t.timestamps
    end
  end

  def self.down
    drop_table :proxies
  end
end
